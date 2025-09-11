"""
Handles application initialization on page load.

This includes:
    - Loading the NAARI configuration from file
    - Polling WLED devices for initial /json and /presets.json data
    - Preparing initial cache and UI state
    - Enabling polling after successful startup

"""

from __future__ import annotations

import logging
import time
import os

from dotenv import load_dotenv
from dash import Input, Output
from dash.exceptions import PreventUpdate

from naari_logging.naari_logger import LogManager
from naari_app.util.wled_device_status import poll_all_devices
from naari_app.util.util_functions import get_devices_ip, device_polled_data_mapping, naari_config_load
from naari_app.util.initial_load import get_initial_load

MAINDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ",,"))
load_dotenv(os.path.join(MAINDIR, ".env"))
TO_LOG = int(os.getenv("LOGGING", "0")) == 1


def startup_callbacks(app):
    """
    Register callbacks related to app startup and page load behavior.

    Includes:
        - Validating or rebuilding the device cache on initial load
        - Enabling polling once cache and settings are ready
    """

    @app.callback(
        [
            Output('naari_settings', 'data', allow_duplicate=True),
            Output('initial_device_catch_data', 'data'),
            Output('devices_catch_presets', 'data', allow_duplicate=True),
            Output('poll_interval', 'disabled'),
            Output('data_app_load_check', 'data')
        ],
        Input('url', 'pathname'),

    )
    # TODO: see if there a way I can send a notification or make a UI change if an error occures.
    def page_data_load(_):
        """
            Triggered on initial page load or reload.

            Loads the NAARI configuration from `naari_config.json`, performs initial GET
            polling of WLED devices, and populates the core app data stores for settings,
            device states, and device presets.

            Also manages a basic retry loop to handle async device startup or polling delays,
            especially in production environments (e.g., Docker container cold starts).
        """

        naari_settings, cach_data, cach_presets = initial_load()

        for _ in range(2):

            if cach_data and all('data' in device for device in cach_data):
                #return False, cach_data, True
                return naari_settings, cach_data, cach_presets, False, True
            LogManager.print_message(
                "Initial polling failed. RE-polling devices",
                to_log=TO_LOG,
                log_level=logging.ERROR
            )

            ip_list = get_devices_ip(
                naari_devices=naari_settings.get('devices'),
                get_inactive=False
            )
            cach_data = poll_all_devices(device_address_list= ip_list)
            time.sleep(2)   # allows for time for async devices to load properly

        # TODO: pop up error needs to be done.
        LogManager.print_message(
            "Unable to get data from all devices",
            to_log=TO_LOG,
            log_level=logging.ERROR
        )
        return naari_settings, None, None, True, False


#---------------Helper Function----------------#

def initial_load():
    """ Loads the NAARI configuration and performs the first poll of all active devices. """
    naari_settings = naari_config_load()

    if not naari_settings:
        LogManager.print_message(
            "Config File unable to load. Check system.",
            to_log=TO_LOG,
            log_level=logging.ERROR
        )
        # TODO: create popup error
        raise PreventUpdate

    # Initial poll fetch
    polled_devices, polled_presets = get_initial_load(naari_devices=naari_settings.get('devices', []))

    # Intentional pause to let devices settle before regular polling starts.
    # (Keeps first render consistent with initial poll results.)
    time.sleep(3)

    if not polled_devices:
        return naari_settings, polled_devices, polled_presets

    # TODO: is there a simplier way to do it than remember to add a funciton to it?
    # Adds device_id to the polled data
    polled_devices = device_polled_data_mapping(
        cach_data=polled_devices,
        devices=naari_settings.get('devices')
    )
    polled_presets = device_polled_data_mapping(
        cach_data=polled_presets,
        devices=naari_settings.get('devices')
    )

    return naari_settings, polled_devices, polled_presets
