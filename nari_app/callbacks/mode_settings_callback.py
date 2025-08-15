import dash.exceptions
from dash import Input, Output, State, html, ALL, callback_context, MATCH

from nari_app.callbacks.status_callbacks import device_preset_list
from nari_app.modals.preset_modal import mode_card

COLLAPSE_OPEN_SYMBOL = html.I(className="bi bi-caret-left-fill fs-5")
COLLAPSE_CLOSE_SYMBOL = html.I(className="bi bi-caret-down-fill fs-5")
BLANK_MODE = {
    "name": None,
    "presets": [
        {
            "device_address": None,
            "preset_name": None
        }
    ]
}

def mode_settings_callback(app):
    # TODO: move into own callback? Preset Setting Clalback
    @app.callback(
        [
            Output({'type': 'mode_card_collapse_element', 'mode_name': ALL}, 'is_open'),
            Output({'type': 'mode_card_collapse_button', 'mode_name': ALL}, 'children'),
            Output({'type': 'mode_card_preset_selection', 'device': ALL, 'mode_name': ALL}, 'options'),
            Output({'type': 'mode_card_preset_selection', 'device': ALL, 'mode_name': ALL}, 'value')
        ],
        [
            Input('config-btn', 'n_clicks'),
            Input({'type': 'mode_card_collapse_button', 'mode_name': ALL}, 'n_clicks')
        ],
        [
            State({'type': 'mode_card_collapse_button', 'mode_name': ALL}, 'n_clicks'),
            State('devices_catch_presets', 'data'),
            State('nari_settings', 'data')
        ]
    )
    def mode_preset_viewable(config_button, pressed_collapse_buttons_value, state_collapse_buttons_value, cach_devices_preset, nari_settings):
        ctx = callback_context

        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        # args_grouping returns inputs/states organized by the wildcard pattern
        # 0: Config Button
        # 1: List of triggered buttons (by ALL)
        # 2: List of the first State (devices_catch_presets)
        trigger_info = ctx.args_grouping

        # Mapping which mode was clicked and how many times it was clicked
        mapping = {f"{element['id']['mode_name']}": element['value'] for element in trigger_info[1]}

        # Building available preset options (used in dropdown) for each device in use
        device_current_presets = {preset_set['ip']: device_preset_list(preset_set) for preset_set in cach_devices_preset}

        # Building the mapping of each mode with the devices
        dropdown_mapping = {f"{element['id']['mode_name']}": device_current_presets for element in trigger_info[1]}

        # Build the outputs
        ############################################

        # If click count is odd, close it; even means open
        button_rep = [COLLAPSE_CLOSE_SYMBOL if value % 2 else COLLAPSE_OPEN_SYMBOL for value in mapping.values()]
        is_open = [False if value % 2 else True for value in mapping.values()]

        # Flatten all preset dropdown options per device for each mode into a single list to be Outputed
        dropdowns_list = [
            preset
            for device_presets in dropdown_mapping.values()
            for preset in device_presets.values()
        ]

        dropdown_values_mapping = {
            mode_name: {
                device_addr: next(
                    # Find the actual dropdown option that matches the saved preset name (based on split)
                    (preset for preset in device_presets if preset == selected),
                    None
                )
                if (selected := next(
                    # Find the preset_name saved for this mode/device in the loaded config
                    (device['preset_name'] for mode in nari_settings['modes'] if mode['name'] == mode_name
                     for device in mode['presets'] if device['device_address'] == device_addr),
                    None
                )) else None
                for device_addr, device_presets in device_map.items()
            }
            for mode_name, device_map in dropdown_mapping.items()
        }

        # Flatten into final list of dropdown selected values (in same order as options list) to be Outputed
        dropdown_values = [
            dropdown_value
            for map in dropdown_values_mapping.values()
            for dropdown_value in map.values()
        ]

        # TODO: Have this as a log inorder to populate list values in the background?

        return is_open, button_rep, dropdowns_list, dropdown_values


    @app.callback(
        Output({'type': 'mode_card_name_element', 'mode_name': MATCH}, 'readonly'),
        Input({'type': 'mode_card_name_edit_element', 'mode_name': MATCH}, 'value')
    )
    def update_mode_name(title_switch):
        if title_switch:
            return False
        return True

    # TODO: move into own callback? Preset Setting Clalback
    @app.callback(
        Output('preset_mode_card_stack', 'children', allow_duplicate=True),
        [
            Input('preset_mode_add_button', 'n_clicks'),
            Input({'type': 'remove_card_element', 'mode_name': ALL}, 'n_clicks')
        ],
        [
            State('preset_mode_card_stack', 'children'),
            State('nari_settings', 'data'),
            #State('elements_initialized', 'data')
        ]
    )
    def add_remove_preset_mode(add_mode_click, remove_mode_clicks, current_children_set, nari_settings):
        ctx = callback_context

        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        triggered = ctx.triggered_id

        if triggered == 'preset_mode_add_button' and add_mode_click:
            # Need to setup the dictionary that will be sent
            new_mode = {
                'name': f"mode_addition_{add_mode_click}",
                'presets': [{"device_address": device['address']} for device in nari_settings['devices']]
            }

            # Creates the Layout that will be Rendered to the current list
            new_card = mode_card(
                mode_preset=new_mode,
                readonly=True
            )

            # Safely appends the new card into the set
            render_set = current_children_set + [new_card]

            return render_set

        elif isinstance(triggered, dict) and triggered['type'] == 'remove_card_element':
            mode_to_remove = triggered['mode_name']

            updated_children = []
            for child in current_children_set:
                if (
                        isinstance(child, dict) and
                        'props' in child and
                        child['props'].get('id', {}).get('type') == 'mode_card' and
                        child['props']['id'].get('mode_name') == mode_to_remove
                ):
                    continue  # Skip this card (i.e., remove it)
                updated_children.append(child)

            return updated_children

        return current_children_set

