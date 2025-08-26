
from __future__ import annotations
import time

from dash import Input, Output, State
from dash.exceptions import PreventUpdate

from nari_app.ui_parts.main_content import main_content
from nari_app.modals.config_modal import config_modal
from nari_app.util.config_builder import NariSettingsConfig
from nari_app.util.wled_device_status import poll_all_devices
from nari_app.util.util_functions import get_devices_ip


def nari_settings_updated(app):
    
    @app.callback(
        [
            Output('poll-interval', 'disabled'),
            Output('initial_device_catch_data', 'data'),
            Output('data_app_load_check', 'data')
        ],
        Input('url', 'pathname'),
        [
            State('initial_device_catch_data', 'data'),
            State('nari_settings', 'data')
        ],
    )
    # TODO: see if there a way I can send a notification or make a UI change if an error occures.
    def page_data_load(_, initial_cach_data, nari_settings):
        """
            On page load/reload, validate or rebuild device cache.
            Enables poller only after cache looks valid.
        """
        if not nari_settings:
            print("nari no go")
            raise PreventUpdate

        cach_data = initial_cach_data
        for _ in range(2):

            if cach_data and all('data' in device for device in cach_data):
                return False, cach_data, True
            print("initial polling failed, extra polling")  # TODO: Log event.

            ip_list = get_devices_ip(
                nari_devices=nari_settings.get('devices'),
                get_inactive=False
            )
            cach_data = poll_all_devices(device_address_list= ip_list)
            time.sleep(2)   # allows for time for async devices to load properly

        # TODO: pop up error needs to be done.
        raise PreventUpdate

    @app.callback(
        [
            Output('room-theme-mode', 'options'),
            Output('app_main_content', 'children'),
            Output('config_modal_container', 'children')
        ],
        Input('nari_settings', 'data'),
    )
    def ui_updated(nari_settings: NariSettingsConfig):
        """
           Rebuild UI sections when `nari_settings` changes. Normally after Config Save.
        """
        themes = nari_settings.get('themes', [])
        theme_options = [ {'label': theme['name'], 'value': theme['id']} for theme in themes ]

        return theme_options, main_content(nari_settings['devices']), config_modal(nari_settings)


