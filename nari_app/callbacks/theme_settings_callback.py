""""
Handles callbacks related to the Theme tab in the Config Modal.

These callbacks manage the theme card UI widgets, including expanding/collapsing
theme sections, assigning per-device presets, editing theme names, and adding
or removing theme cards.

All behavior in this module is scoped to UI and state changes within the
configuration interface — no live device commands are issued.
"""

import dash.exceptions
from dash import Input, Output, State, html, ALL, ctx, MATCH

from nari_app.callbacks.status_callbacks import device_preset_list
from nari_app.modals.theme_settings_tab import theme_card
from nari_app.util.config_builder import NariSettingsConfig


# TODO: move this into master call class?
COLLAPSE_OPEN_SYMBOL = html.I(className="bi bi-caret-left-fill fs-5")
COLLAPSE_CLOSE_SYMBOL = html.I(className="bi bi-caret-down-fill fs-5")


def theme_settings_callback(app):
    """
        Register callbacks for the Theme Settings tab in the Config Modal.

        Includes:
            - Toggling collapsible sections for each theme
            - Populating per-device preset dropdowns for each theme
            - Enabling or disabling theme name editing
            - Adding or removing theme cards from the stack
    """
    @app.callback(
        [
            Output({'type': 'theme_collapse_element', 'theme_id': ALL}, 'is_open'),
            Output({'type': 'theme_card_collapse_button', 'theme_id': ALL}, 'children'),
            Output({'type': 'theme_device_preset_selection', 'theme_id': ALL, 'device_id': ALL}, 'options'),
            Output({'type': 'theme_device_preset_selection', 'theme_id': ALL, 'device_id': ALL}, 'value')
        ],
        Input({'type': 'theme_card_collapse_button', 'theme_id': ALL}, 'n_clicks'),
        [
            State('devices_catch_presets', 'data'),
            State('nari_settings', 'data')
        ]
    )
    def theme_device_preset_viewable(pressed_collapse_buttons_value, cach_devices_preset, nari_settings):
        """ Toggle theme card collapses and populate per‑device preset dropdowns for each theme. """
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        # Snapshot of current UI state to align mappings with the active layout
        widget_layout = ctx.inputs_list[0]

        collapse_clicks_mapping = {element['id']['theme_id']: element['value'] for element in widget_layout}

        current_config_devices_list = [device['id'] for device in nari_settings['devices']]

        device_current_presets_mapping = {preset_set['device_id']: device_preset_list(preset_set) for preset_set in cach_devices_preset if preset_set['device_id'] in current_config_devices_list}

        dropdown_options_mapping = {element['id']['theme_id']: device_current_presets_mapping for element in widget_layout}

        is_open_list = [not bool(value % 2) for value in collapse_clicks_mapping .values()]     # pylint suggestion.
        button_children_list  = [COLLAPSE_CLOSE_SYMBOL if value % 2 else COLLAPSE_OPEN_SYMBOL for value in collapse_clicks_mapping .values()]

        # Lists needs to be flatten in order for Dash to output.
        dropdowns_options_flatten = [
            presets
            for device_presets in dropdown_options_mapping.values()
            for presets in device_presets.values()
        ]

        dropdown_values_mapping = compute_dropdown_values_mapping(dropdown_options_mapping, nari_settings)

        # Flatten values to mirror the same theme/device order used for options:
        dropdown_values = [
            dropdown_values_mapping[theme_id].get(device_id, "")
            for theme_id, device_map in dropdown_options_mapping.items()
            for device_id in device_map.keys()
        ]

        # Handle inactive/down devices: keep existing selection if no options present.
        #   Prevents blanks from being saved by accident.
        for index, selections in enumerate(dropdowns_options_flatten):
            if len(selections) == 0:
                dropdowns_options_flatten[index] = [dropdown_values[index]] if len(dropdown_values[index]) else ""

        # TODO: Have this as a log inorder to populate list values in the background?
        return is_open_list, button_children_list, dropdowns_options_flatten, dropdown_values


    @app.callback(
        Output({'type': 'theme_name_input', 'theme_id': MATCH}, 'readonly'),
        Input({'type': 'theme_name_edit', 'theme_id': MATCH}, 'value')
    )
    def update_theme_name(title_switch):
        """ Makes the theme name field editable if the edit toggle is on, otherwise keeps it read-only. """
        if title_switch:
            return False
        return True

    @app.callback(
        Output('theme_cards_stack', 'children', allow_duplicate=True),
        [
            Input('theme_add_button', 'n_clicks'),
            Input({'type': 'theme_delete', 'theme_id': ALL}, 'n_clicks')
        ],
        [
            State('theme_cards_stack', 'children'),
            # Doesn't matter what to use as long as it has 'theme_id'
            Input({'type': 'theme_delete', 'theme_id': ALL}, 'id'),
            State('nari_settings', 'data'),
        ],
    )
    def add_remove_theme_card(add_mode_click, remove_mode_clicks, current_children_set, removed_widgets, nari_settings):
        """Add a new theme card or remove an existing one in the Theme Settings stack."""
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        triggered = ctx.triggered_id

        if triggered == 'theme_add_button' and add_mode_click:          # pylint: disable=no-else-return
            existing_theme_ids = (widget['theme_id'] for widget in removed_widgets )
            next_id = (max(existing_theme_ids) + 1) if existing_theme_ids else 1        # pylint: disable=using-constant-test

            default_presets_for_system_devices = [
                {
                    'device_id': device['id'],
                    'device_address': device['address'],
                    'preset_name': ""
                }
                for device in nari_settings['devices']
            ]

            new_theme = {
                'id': next_id,
                'name': f"mode_addition_{add_mode_click}",
                'presets': default_presets_for_system_devices
            }

            new_card = theme_card(
                theme_info=new_theme,
                devices=nari_settings['devices'],
                readonly=True,
                init_load=False
            )

            # Allows for a safe appendage of card to stack layout.
            render_set = current_children_set + [new_card]

            return render_set

        elif isinstance(triggered, dict) and triggered['type'] == 'theme_delete':        # pylint: disable=no-else-return
            theme_to_remove = triggered['theme_id']

            updated_children = []
            for child in current_children_set:
                if (
                        isinstance(child, dict) and
                        'props' in child and
                        child['props'].get('id', {}).get('type') == 'theme_card' and
                        child['props'].get('id', {}).get('theme_id') == theme_to_remove
                ):
                    continue  # Skip this card (i.e., remove it)
                updated_children.append(child)

            return updated_children
        return current_children_set

#-------------------------------------Helper Functions----------------------------------------------#

def compute_dropdown_values_mapping(dropdown_options_mapping: dict, nari_settings: NariSettingsConfig) -> dict[int, dict[int, str]]:
    """theme_id -> { device_id -> selected_value } with config as source of truth."""
    # Note: Saved presets values from config file.
    saved = {
        (theme['id'], preset['device_id']): preset['preset_name']
        for theme in nari_settings.get('themes', [])
        for preset in theme.get('presets', [])
    }

    values_by_theme = {}
    for theme_id, device_map in dropdown_options_mapping.items():
        per_theme = {}
        for device_id, options in device_map.items():
            saved_value = saved.get((theme_id, device_id))

            if saved_value is not None:
                # If offline (no options polled) or saved is still a valid option → keep saved
                if not options or saved_value in options:
                    per_theme[device_id] = saved_value
                else:
                    # Options exist but saved isn't present anymore → pick first option
                    per_theme[device_id] = options[0]
            else:
                # New theme/device row (no saved value) → default to ""
                per_theme[device_id] = ""

        values_by_theme[theme_id] = per_theme
    return values_by_theme
