"""
Handles application refresh logic in response to configuration updates.

This includes:
    - Rebuilding layout components (main content, config modal, theme options)
    - Polling WLED devices for status and preset data for intial page load
    - Updating internal caches and polling interval when Refresh button is triggered
    - Displaying success/failure messages for refresh events
"""

from __future__ import annotations

import time
import os
import logging

from dotenv import load_dotenv
from dash import Input, Output, State, ctx
from dash.exceptions import PreventUpdate

from naari_logging.naari_logger import LogManager
from naari_app.ui_parts.main_content import main_content
from naari_app.modals.config_modal import config_modal
from naari_app.util.config_builder import NaariSettingsConfig, DeviceConfig
from naari_app.util.wled_device_status import PollingThreadLock, get_devices_ip, poll_all_devices, poll_device_presets
from naari_app.util.util_functions import device_polled_data_mapping

__all__=['refresh_callbacks']

MAINDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ",,"))
load_dotenv(os.path.join(MAINDIR, ".env"))
TO_LOG = int(os.getenv("LOGGING", "0")) == 1


def refresh_callbacks(app):
    """
        Register callbacks that refresh the app after configuration changes.

        These callbacks handle:
            - Rebuilding UI components after config updates
            - Polling WLED devices for status and preset data
            - Updating internal caches and polling rate
            - Triggering user-facing popups for refresh feedback
    """
    @app.callback(
        [
            Output('room-theme-mode', 'options'),
            Output('app_main_content', 'children'),
            Output('config_modal_container', 'children'),
            Output('refresh_chain_trigger', 'n_clicks', allow_duplicate=True)
        ],
        Input('naari_settings', 'data'),
        State('refresh_chain_trigger', 'n_clicks'),
        prevent_initial_call=True
    )
    def ui_updated(naari_settings: NaariSettingsConfig, refresh_button_clicks):
        """ Rebuild UI sections when `naari_settings` changes. Normally after Config Save. """

        LogManager.print_message(
            "UI Update triggered",
            to_log=TO_LOG
        )

        themes = naari_settings.get('themes', [])
        theme_options = [{'label': theme['name'], 'value': theme['id']} for theme in themes if themes]

        return theme_options, main_content(naari_settings.get('devices', [])), config_modal(naari_settings), refresh_button_clicks + 1


    @app.callback(
        [
            Output('poll_interval', 'disabled', allow_duplicate=True),
            Output("refresh_chain_trigger", 'n_clicks')
        ],
        Input('refresh_button', 'n_clicks'),
        State("refresh_chain_trigger", 'n_clicks'),
        prevent_initial_call=True
    )
    def refresh_trigger(_, refresh_trigger):
        if not ctx.triggered:
            raise PreventUpdate

        LogManager.print_message(
            "refresh triggered",
            to_log=TO_LOG
        )

        return True, refresh_trigger + 1


    @app.callback(
        [
            Output('data_app_load_check', 'data'),
            Output("refresh_popup", 'is_open'),
            Output('refresh_popup', 'color'),
            Output('refresh_popup', 'children'),
            Output('poll_interval', 'disabled', allow_duplicate=True),
            Output('poll_interval', 'interval', allow_duplicate=True),
            Output('reset_poll_interval', 'data', allow_duplicate=True),
            Output('device_catch_data', 'data', allow_duplicate=True),
            Output('devices_catch_presets', 'data', allow_duplicate=True),
            Output('brightness_chain_trigger', 'n_clicks'),
        ],
        Input('refresh_chain_trigger', 'n_clicks'),
        [
            State('data_app_load_check', 'data'),
            State('brightness_chain_trigger', 'n_clicks'),
            State('naari_settings', 'data')
        ],
        prevent_initial_call=True
    )
    def refresh_data(_, app_loaded, brightness_chain_trigger, naari_settings):
        """
            Poll all active (or all known) devices and update app data stores.

            Triggered by refresh_chain_trigger, this function:
                - Polls WLED devices for /json and /presets.json
                - Updates device and preset caches
                - Adjusts polling interval if required
                - Displays popup feedback about polling success or failures
        """
        if not ctx.triggered:
            raise PreventUpdate

        LogManager.print_message(
            "Data being Refresh/loaded triggered",
            to_log=TO_LOG
        )

        # popup_open is currently service two functions
        #   1) on initial page or naari config update, no need to populate a popup
        #   2) on initial load we do want everything polled for config modular UI population
        popup_open = app_loaded
        force_poll_all = not app_loaded

        current_interval_time = naari_settings['ui_settings']['polling_rate']['value']
        poll_interval_disabled = False

        for tries in range(2):
            try:
                cache_data, cache_presets, polling_time = data_load(
                    naari_devices=naari_settings.get('devices'),
                    get_all_devices= force_poll_all
                )
                break
            except PollingThreadLock:
                if tries >= 1:
                    cache_data, cache_presets, polling_time = [], [], current_interval_time * 2


        # Adjust polling time if an error or timeout occures.
        # Aids in preventing polling lock
        if polling_time > current_interval_time:
            current_interval_time = polling_time + 2  # converts to ms per dcc.Interval rules

        data_poll_ok = cache_data and all ('data' in device for device in cache_data)
        presets_poll_ok = cache_presets and all('data' in device for device in cache_presets)

        error_message = []
        popup_message = []
        popup_color = 'info'

        if data_poll_ok and presets_poll_ok:
            popup_message = "Re-Loaded"
            popup_color = 'success'

        if not presets_poll_ok:
            failed_devices_polled = [f"{device['ip']}:{device['error_type']}" for device in cache_presets if device.get('error', False)]
            message = "Some presets failed to load: " + ",".join(failed_devices_polled)
            error_message.append(message)
            popup_message.append("Some devices failed to load presets")

        if not data_poll_ok:
            failed_devices_polled = [f"{device['ip']}:{device['error_type']}" for device in cache_data if device.get('error', False)]
            message = "Some devices data failed to load: " + ",".join(failed_devices_polled)
            error_message.append(message)
            popup_message.append("Some devices failed to load data")

        if error_message:
            error_message = "\n".join(error_message)
            popup_message = " & ".join(popup_message)
            LogManager.print_message(
                error_message,
                to_log=TO_LOG,
                log_level=logging.ERROR
            )

        # After multiple attempts we get nothing?
        # TODO: Popup here
        if not cache_data and not cache_presets:
            error_message = "Refresh failed check devices and previous error message"
            popup_color = 'danger'
            popup_message = "Polling Failed"
            poll_interval_disabled = True
            LogManager.print_message(
                error_message,
                to_log=TO_LOG,
                log_level=logging.CRITICAL
            )

        reset_poll_interval = True
        return (True, popup_open, popup_color, popup_message, poll_interval_disabled, current_interval_time * 1000, reset_poll_interval,
        cache_data, cache_presets, brightness_chain_trigger + 1)

#---------- Helper Functions------------------------#

def data_load(naari_devices: list[DeviceConfig], get_all_devices: bool = True, add_wait: int = 0):
    """
    Polls WLED devices and returns mapped status and preset data.

    Args:
        naari_devices: List of devices from the config.
        get_all_devices: Whether to include inactive devices in polling.
        add_wait: Optional pause after polling to allow device reset time.

    Returns:
        tuple: (status_data, preset_data, polling_time)
    """

    device_ips = get_devices_ip(
        naari_devices=naari_devices,
        get_inactive=get_all_devices  # accommodate for initial and manual mode.
    )

    try:
        cach_data, polling_time = poll_all_devices(device_ips)
    except PollingThreadLock:
        raise PollingThreadLock

    time.sleep( 1 + add_wait )   # Intentional pause as tests shows devices need moment to reset/rest after polling.
    cach_preset = poll_device_presets(device_ips)

    # Adds device_id to the polled data
    polled_devices = device_polled_data_mapping(
        cach_data=cach_data,
        devices=naari_devices
    )

    polled_presets = device_polled_data_mapping(
        cach_data=cach_preset,
        devices=naari_devices
    )

    return polled_devices, polled_presets, polling_time
