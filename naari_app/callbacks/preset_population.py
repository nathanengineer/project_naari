"""
Handles UI population of preset dropdowns for each WLED device card.

This module listens for updated preset data and maps it to the
corresponding UI card elements in the app.
"""

from dash import Input, Output, State, ALL, ctx
from dash.exceptions import PreventUpdate


def preset_callbacks(app):
    """ Register callbacks for populating preset selection dropdowns for each device card in the UI. """
    @app.callback(
        Output({'type': 'preset_selection', 'device_id': ALL}, 'options'),
        Input('devices_catch_presets', 'data'),
        [
            State({'type': 'device_card', 'device_id': ALL}, 'id'),
            State('data_app_load_check', 'data')
        ]
    )
    def update_preset_dropdowns(devices_catch_presets_data, device_cards_id, app_load_check):
        """
        Populates the preset dropdowns for each active device card
        based on the cached preset data from polled WLED devices.

        Dropdown options are ordered to match the layout of device cards.
        """

        # Prevent dropdown updates during initial load or invalid context
        if not ctx.triggered or not app_load_check:
            raise PreventUpdate

        card_device_ids = [ card['device_id'] for card in device_cards_id ]

        ordered_presets = []
        for dev_id in card_device_ids:
            matching_presets = next(
                (device_preset_list(p) for p in devices_catch_presets_data if p['device_id'] == dev_id),
                []
            )
            ordered_presets.append(matching_presets)

        return ordered_presets

#---------- Helper Functions------------------------#

def device_preset_list(device_presets):
    """ Requires results from Polling Presets off devices"""
    #presets = [presets.get('data', None) for presets in device_preset if presets['ip'] == ip_name][0]
    presets = device_presets.get('data', None)
    if not presets:
        return []
    preset_sorted = {
        int(k): v
        for k, v in sorted(
            ((k, val.get('n', None)) for k, val in presets.items()),
            key=lambda item: (item[1] is None, str(item[1]).lower())
        )
    }
    return [f"{key}: {value}" for key, value in preset_sorted.items()]
