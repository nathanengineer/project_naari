from dash import Input, Output, State
from dash.exceptions import PreventUpdate

from nari_app.ui_parts.main_content import main_content
from nari_app.modals.config_modal import config_modal
from nari_app.util.wled_device_status import poll_all_devices


def nari_settings_updated(app):

    @app.callback(
        [
            Output('poll-interval', 'disabled'),
            Output('initial_device_catch_data', 'data'),
            Output('data_app_load_check', 'data')
        ],
        Input('url', 'pathname'),
        State('initial_device_catch_data', 'data'),
    )
    # TODO: see if there a way I can send a notification or make a UI change if an error occures.
    def page_load(page_load, initial_device_catch_data):
        device_catch_data = initial_device_catch_data
        for _ in range(2):
            if device_catch_data and all('data' in device for device in device_catch_data):
                return False, device_catch_data, True
            print("extra polling")
            device_catch_data = poll_all_devices()
            # await asyncio.sleep(2)

        # TODO: pop up error needs to be done.
        raise PreventUpdate

    @app.callback(
        [
            Output('room-theme-mode', 'options'),
            Output('app_main_content', 'children'),
            Output('config_modal_container', 'children'),
        ],
        Input('nari_settings', 'data'),
    )
    def settings_updated(nari_settings):
        theme_options = [selection['name'] if selection['name'] else "" for selection in nari_settings['modes']]
        return theme_options, main_content(nari_settings['devices']), config_modal(nari_settings)


