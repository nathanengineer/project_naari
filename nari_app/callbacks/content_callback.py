from dash import Input, Output, State, ALL

from nari_app.util.util_functions import is_app_loaded

DEVICE_IDS = []

def main_content_callback(app):

    @app.callback(
        Output({'type': 'collapse_segment', 'device': ALL}, 'is_open'),
        Input({'type': 'device_collapse_button', 'device': ALL}, 'n_clicks'),
        [State("devices_catch_presets", "data"),
         State("elements_initialized", 'data')]
    )
    @is_app_loaded()
    def collapse_element(clicks, cach_data, _):
        devices_id = [device['ip'] for device in cach_data]
        # TODO: is this useful for logging
        click_map = dict(zip(devices_id, clicks))

        # Even = True (collapse element = open)
        # Odd = False (collapse element = close)
        status_map = {device: (click % 2 == 0) for device, click in zip(devices_id, clicks)}

        return list(status_map.values())





