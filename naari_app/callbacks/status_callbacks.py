"""
Handles polling and device status update callbacks.

These callbacks collect data from WLED devices through GET requests and update the UI accordingly.
"""

import os
import logging
import math

from dotenv import load_dotenv
from dash import Input, Output, State, ALL, ctx
from dash.exceptions import PreventUpdate

from naari_logging.naari_logger import LogManager
from naari_app.util.config_builder import NaariSettingsConfig
from naari_app.util.wled_device_status import PollingThreadLock, get_devices_ip, poll_all_devices, get_status
from naari_app.util.send_payload import send_device_power_update, PayloadRetryError
from naari_app.util.util_functions import device_polled_data_mapping, is_device_active, get_device

MAINDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ",,"))
load_dotenv(os.path.join(MAINDIR, ".env"))
TO_LOG = int(os.getenv("LOGGING", "0")) == 1


def status_callbacks(app):      # pylint: disable=too-many-statements
    """
       Register callbacks responsible for polling device data
       and updating UI status indicators.

       Includes:
           - Polling devices for /json and /presets.json data
           - Populating UI elements with current presets
           - Updating visual status of power buttons based on polled results
    """

    @app.callback(
        [
            Output('poll_interval', 'n_intervals'),
            Output('reset_poll_interval', 'data', allow_duplicate=True)
        ],
        Input('reset_poll_interval', 'data'),
        prevent_initial_call=True
    )
    def reset_polling_interval(reset_poll_interval):
        """ Reset Polling idle throttle. """
        LogManager.print_message(
            "polling interval restet triggered",
            to_log=TO_LOG
        )

        if reset_poll_interval:
            return 0, False
        raise PreventUpdate


    @app.callback(
        [
            Output('device_catch_data', 'data'),
            Output('poll_interval', 'interval', allow_duplicate=True)
        ],
        Input('poll_interval', 'n_intervals'),
        State('naari_settings', 'data'),
        prevent_initial_call=True
    )
    # TODO: see if there a way I can send a notification or make a UI change if an error occures.
    def poll_devices(n_interval, naari_settings):
        """ Callback function responsible for acquiring data from devices based on interval. Has built in idle throttle. """
        if not ctx.triggered:
            raise PreventUpdate

        LogManager.print_message(
            "Polling device interval triggered",
            to_log=TO_LOG
        )

        poll_allowed = poll_interval_trigger(
            elapsed_interval=n_interval,
            naari_config=naari_settings
        )

        if ctx.triggered_id == 'poll_interval' and poll_allowed:
            ip_list = get_devices_ip(
                naari_devices=naari_settings.get('devices'),
                get_inactive=False
            )

            current_interval_time = naari_settings['ui_settings']['polling_rate']['value']
            try:
                catch_data, polling_time = poll_all_devices(device_address_list= ip_list)

                if polling_time > current_interval_time:
                    current_interval_time = (polling_time + 2)

                catch_data = device_polled_data_mapping(
                    cach_data=catch_data,
                    devices=naari_settings.get('devices')
                )

                if catch_data and all('data' in device for device in catch_data):
                    # TODO: polling_error_counter = 0
                    return catch_data, current_interval_time * 1000

            except PollingThreadLock:
                # TODO: polling_error_counter =+ 1
                # TODO: Popup if multiple repeats
                raise PreventUpdate

            return catch_data, current_interval_time * 1000
        raise PreventUpdate


    @app.callback(
        [
            Output({'type': 'power_button', 'device_id': ALL}, 'color'),
            Output('reset_poll_interval', 'data', allow_duplicate=True)
        ],
        [
            Input("device_catch_data", "data"),
            Input({'type': 'power_button', 'device_id': ALL}, 'n_clicks')
        ],
        [
            Input({'type': 'power_button', 'device_id': ALL}, 'id'),
            State("device_catch_data", "data"),
            State('poll_interval', 'n_intervals'),
            State('naari_settings', 'data'),
            State('reset_poll_interval', 'data')
        ],
        prevent_initial_call=True,
    )
    def device_power_button_status(polled_data, _power_button_press, power_button_ids, cached_device_data, poll_interval,         # pylint: disable=possibly-used-before-assignment, too-many-positional-arguments, too-many-locals
        naari_settings, reset_poll_interval):
        """ Updates the Power Button widget color based on if device is on or off. """

        # Nothing polled yet? Don’t render.
        if not cached_device_data or not isinstance(cached_device_data, list):
            LogManager.print_message(
                "No polled data to determine power status:: %s",
                str(cached_device_data),
                to_log=TO_LOG,
                log_level=logging.ERROR
            )
            raise PreventUpdate

        if not ctx.triggered:
            raise PreventUpdate

        triggered_id = ctx.triggered_id

        LogManager.print_message(
            "power button status triggered",
            to_log=TO_LOG
        )

        if isinstance(triggered_id, dict) and triggered_id['type'] == 'power_button':   # Button Click / Manual Entry
            devices_cach_data = cached_device_data
            target_device = get_device(
                devices=naari_settings['devices'],
                device_id=triggered_id['device_id']
            )

        elif triggered_id == 'device_catch_data':       # For Poll-Intervals
            devices_cach_data = polled_data
            target_device = None

        else:
            raise PreventUpdate

        ui_devices_order = [ card['device_id'] for card in power_button_ids ]

        # Ensuring that polled data matches what will be output in the UI
        # Use the UI-rendered order to map ids -> values robustly
        order_poll_data = []
        for dev_id in ui_devices_order:
            matching_presets = next(
                (device_data for device_data in devices_cach_data if device_data['device_id'] == dev_id),
                {}  # ensures something is added if there no device for that card.
            )
            order_poll_data.append(matching_presets)

        # Safely extract on/off state
        # {device_id: True/False/Err}
        indicator_status = {
            entry.get('device_id'): (
                get_status(
                    entry=entry,
                    path=['data', 'state', 'on'],
                    default=None,
                    return_error=True
                )
            )
            for entry in order_poll_data
        }

        # If a button was clicked, toggle that device and update the map
        # To prevent initial trigger poll_interval used.
        if target_device and poll_interval:
            target_id = target_device['id']

            if indicator_status[target_id] is not None and not isinstance(indicator_status[target_id], dict):
                new_state = not indicator_status[target_id]
                try:
                    # TODO: Add api request handler/popup
                    api_response = send_device_power_update(
                        status_update=new_state,
                        device_info=target_device,
                        ui_settings=naari_settings['ui_settings']
                    )
                    indicator_status[target_id] = new_state
                except PayloadRetryError as err:
                    # Keep previous state (color) and log rich context
                    LogManager.print_message(
                        "Power toggle failed after %s attempts (url=%s): %s",
                        getattr(err, "attempts", "n/a"),
                        getattr(err, "url", "n/a"),
                        getattr(err, "last_exception", err),
                        to_log=TO_LOG,
                        log_level=logging.ERROR
                    )
                    # TODO: add trigger indicating what device had an error?

                except Exception as err:       # pylint: disable=broad-exception-caught
                    # Truly unexpected—log & keep previous state
                    LogManager.print_message(
                        "Unexpected error toggling device %s >> %s",
                        (target_id, err),
                        to_log=TO_LOG,
                        log_level=logging.ERROR
                    )
                    # leave state_map[target_id] unchanged
                reset_poll_interval = True  # Resets polling intervals after push event

        # Map in exact UI order; safe fallback when state missing/None
        power_buttons_color = [button_indicator(indicator_status[device_id], device_id) for device_id in ui_devices_order ]

        return power_buttons_color, reset_poll_interval


#---------- Helper Functions------------------------#


def poll_interval_trigger(elapsed_interval: int, naari_config: NaariSettingsConfig) -> bool:
    """
        Determine whether a poll event should trigger based on elapsed time,
        base polling rate, and number of devices.
    """

    #if elapsed_interval > 0:
    # safely pull ui_settings
    ui_settings = naari_config.get("ui_settings", {})

    polling_rate = ui_settings.get("polling_rate",3).get("value", 3)
    max_time = ui_settings.get("max_time", 3600)
    min_time = ui_settings.get("min_time", 60)

    device_count = len(naari_config.get("devices", []))
    elapsed_time = polling_rate * elapsed_interval

    # staged growth thresholds (seconds : multiplier)
    thresholds = [
        (max_time, 4),  # after max_time (default 1h)
        (min_time, 2),  # after min_time (default 1m)
        (0, 1),  # default
    ]

    # pick the first matching threshold
    chosen_mod = next(mod for limit, mod in thresholds if elapsed_time >= limit)

    # adjust for device count > 10
    if device_count > 10:
        chosen_mod = math.ceil(chosen_mod * 1.5)

    # trigger condition
    return elapsed_time % chosen_mod == 0


def button_indicator(indicator: bool | str, device_id: int) -> str:
    """ Contains the different Indicator color depending on status. """
    if isinstance(indicator, dict) and indicator.get("error"):      # pylint: disable=no-else-return
        error_type = indicator['error']['error_type']
        error_message = indicator['error']['error_message']
        match error_type:
            case "invalid_json":
                message = "Poll Data issue for device id {%s} >> get.invalid_json :: %s"
                args = (device_id, error_message)
                color = "dark"

            case "ConnectTimeout":
                message ="ConnectTimeout for device id = %s"
                args = device_id
                color = "warning"

            case _:
                message = "Mass Error in button Indicator from device_id = %s >> %s"
                args = error_message
                color = "dark"

        LogManager.print_message(
            message,
            args,
            to_log=TO_LOG,
            log_level=logging.CRITICAL
        )
        return color

    elif indicator:
        return "success"    # Devices ON

    elif indicator is False:
        return "danger"     # Devices Off

    else:
        LogManager.print_message(
            "Mass Error in button Indicator >> device_id = %s",
            device_id,
            to_log=TO_LOG,
            log_level=logging.CRITICAL
        )
        return "dark"       # Error of some kind
