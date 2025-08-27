"""
Handles page load initialization for the app.

This includes the following functionalities:
    - Validating or rebuilding the device cache
    - Preparing initial settings and enabling key functionality
    - Pulling the initial app configuration settings

"""

from __future__ import annotations
import time

from dash import Input, Output, State
from dash.exceptions import PreventUpdate


from naari_app.util.wled_device_status import poll_all_devices
from naari_app.util.util_functions import get_devices_ip


def startup_callbacks(app):
    """
    Register callbacks related to app startup and page load behavior.

    Includes:
        - Validating or rebuilding the device cache on initial load
        - Enabling polling once cache and settings are ready
    """

    @app.callback(
        [
            Output('poll-interval', 'disabled'),
            Output('initial_device_catch_data', 'data'),
            Output('data_app_load_check', 'data')
        ],
        Input('url', 'pathname'),
        [
            State('initial_device_catch_data', 'data'),
            State('naari_settings', 'data')
        ],
    )
    # TODO: see if there a way I can send a notification or make a UI change if an error occures.
    def page_data_load(_, initial_cach_data, naari_settings):
        """
            On page load/reload, validate or rebuild device cache.
            Enables poller only after cache looks valid.
        """
        if not naari_settings:
            print("naari no go")
            raise PreventUpdate

        cach_data = initial_cach_data
        for _ in range(2):

            if cach_data and all('data' in device for device in cach_data):
                return False, cach_data, True
            print("initial polling failed, extra polling")  # TODO: Log event.

            ip_list = get_devices_ip(
                naari_devices=naari_settings.get('devices'),
                get_inactive=False
            )
            cach_data = poll_all_devices(device_address_list= ip_list)
            time.sleep(2)   # allows for time for async devices to load properly

        # TODO: pop up error needs to be done.
        raise PreventUpdate
