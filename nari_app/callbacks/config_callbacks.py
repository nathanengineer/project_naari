import json

import dash.exceptions
from dash import Input, Output, State, ALL, callback_context

from nari_app.util.util_functions import save_configer


BLANK_MODE = {
    "name": None,
    "presets": [
        {
            "device_address": None,
            "preset_name": None
        }
    ]
}

def config_callbacks(app):
    @app.callback(
        [
            Output('modals', 'is_open'),
            Output('preset_mode_add_button', 'n_clicks'),
            Output('preset_mode_card_stack', 'children', allow_duplicate=True),

        ],
        [
            Input('config-btn', 'n_clicks'),
            Input('config_save_button', 'n_clicks'),
            Input('config_cancel_button', 'n_clicks')
        ],
        [
            State('preset_mode_card_stack', 'children'),
            State('data_app_load_check', 'data')
        ],
        prevent_initial_call=True

    )
    def open_model(open_button, save_button, close_button, current_mode_children_set, data_app_load_check):
        ctx = callback_context

        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        trigger_id = ctx.triggered_id

        #match trigger_id:
        #if trigger_id == 'url':
        #    return False, 0, current_mode_children_set

        if data_app_load_check and trigger_id =='config-btn':
            return True, 0, current_mode_children_set

        elif data_app_load_check and data_app_load_check and trigger_id == 'config_save_button':
            return False, 0, current_mode_children_set

        elif data_app_load_check and trigger_id == 'config_cancel_button':
            updated_children = []
            for child in current_mode_children_set:
                if (
                        isinstance(child, dict) and
                        'props' in child and
                        child['props'].get('id', {}).get('type') == 'mode_card' and
                        "mode_addition_" in child['props']['id'].get('mode_name')
                ):
                    continue  # Skip this card (i.e., remove it)
                updated_children.append(child)
            return False, 0, updated_children

        else:
            print(f"open_model function trigger unknown: {trigger_id}")
            raise  dash.exceptions.PreventUpdate


    @app.callback(
        Output('nari_settings', 'data'),
        Input('config_save_button', 'n_clicks'),
        [
            State({'type': 'mode_card_name_element', 'mode_name': ALL}, 'value'),
            State({'type': 'mode_card_name_element', 'mode_name': ALL}, 'id'),
            State({'type': 'mode_card_preset_selection', 'device': ALL, 'mode_name': ALL}, 'value'),
            State({'type': 'mode_card_preset_selection', 'device': ALL, 'mode_name': ALL}, 'id'),
            State('polling_input', 'value'),
            State('master_sync_device', 'value'),
            State({'type': 'device_name', 'device_name': ALL}, 'value'),
            State({'type': 'device_ip_address', 'device_name': ALL}, 'value'),
            State({'type': 'device_instance_name', 'device_name': ALL}, 'value'),
            State('nari_settings', 'data'),
            State('data_app_load_check', 'data')
        ]
    )
    def save_config(save_button, mode_names, mode_name_ids, dropdown_values, dropdown_ids, polling_value, master_sync_device, device_names, device_ip_addresses,
        device_instance_names, current_config, data_app_load_check):

        ctx = callback_context

        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        # args_grouping returns inputs/states organized by the wildcard pattern

        trigger_info = ctx.args_grouping

        print(trigger_info[3])

        if data_app_load_check:
            # If any of the cards was open dropdown values in the preset mode modular will be populated.
            # Thus only currently known settings would be saved or updated versions.
            print(dropdown_values)
            if all(dropdown_values):
                new_modes = {}
                mode_name_map = {
                    id_obj['mode_name']: name_value
                    for id_obj, name_value in zip(mode_name_ids, mode_names)
                }

                for value, comp_id in zip(dropdown_values, dropdown_ids):
                    mode_key = comp_id['mode_name']
                    device_address = comp_id['device']
                    preset_name = value if value else ""    # Keeping this one line to reduce boilerplate

                    if mode_key not in new_modes:
                        new_modes[mode_key] = []

                    new_modes[mode_key].append({
                        'device_address': device_address,
                        'preset_name': preset_name
                    })

                updated_modes = [
                    {
                        'name': mode_name_map[mode_key],
                        'presets': preset_list
                    }
                    for mode_key, preset_list in new_modes.items()

                ]

                updated_modes.append(BLANK_MODE)

                current_config['modes'] = updated_modes

            # Segemtn for Polling Settings
            if polling_value != current_config['ui_settings']['polling_rate'] and polling_value >= 3:
                current_config['ui_settings']['polling_rate'] = polling_value

            # Segment for saving new Master Sync Device
            master_sync_device = json.loads(master_sync_device)     # Need to convert back into dict from serialized version
            if master_sync_device != current_config['master_device']:
                current_config['master_device'] = master_sync_device

            # Populating possible new Devices to our configure
            nari_devices = [
                {
                "name": device_name,
                "address": device_address,
                "instance_name": device_instance_name
                }
                for device_name, device_address, device_instance_name in zip(device_names, device_ip_addresses, device_instance_names)
            ]

            # TODO: Log when an update occured.
            if find_new_device(current_config['devices'], nari_devices):
                current_config['devices'] = nari_devices


            save_configer(current_config)

            return current_config

        return current_config



def find_new_device(old_list, new_list) -> bool:
    old_map = {device['name']: device for device in old_list}
    new_map = {device['name']: device for device in new_list}
    return old_map != new_map


