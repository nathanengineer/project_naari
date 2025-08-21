""" Modular that handles the backend callbacks of the Config Modal. """

from dash.exceptions import PreventUpdate
from dash import Input, Output, State, ALL, ctx

from nari_app.util.util_functions import save_configer
from nari_app.util.config_builder import DeviceConfig, UISettings, ThemeSelectionConfig, NariSettingsConfig


def config_callbacks(app):
    @app.callback(
        [
            Output("config_modal", 'is_open'),
            Output('theme_add_button', 'n_clicks'),
            Output('theme_cards_stack', 'children', allow_duplicate=True),
            Output('device_add_button', 'n_clicks'),
            Output('devices_stack', 'children', allow_duplicate=True)
        ],
        [
            Input('config-btn', 'n_clicks'),
            Input('config_save_button', 'n_clicks'),
            Input('config_cancel_button', 'n_clicks')
        ],
        [
            State('theme_cards_stack', 'children'),
            State('devices_stack', 'children')
        ],
    )
    def open_model(open_button, save_button, close_button, current_themes_children_set, current_devices_children_set):
        """ Handles the opening and closing of the Modal. For when someone clicks Cancel, will revert back to previous state. """
        if not ctx.triggered:
            raise PreventUpdate

        trigger_id = ctx.triggered_id

        #if data_app_load_check and trigger_id == 'config-btn':
        if trigger_id == 'config-btn':                                                                          # pylint: disable=no-else-return
            return True, 0, current_themes_children_set, 0, current_devices_children_set

        #elif data_app_load_check and data_app_load_check and trigger_id == 'config_save_button':
        elif trigger_id == 'config_save_button':                                                                # pylint: disable=no-else-return
            return False, 0, current_themes_children_set, 0, current_devices_children_set

        #elif data_app_load_check and trigger_id == 'config_cancel_button':
        elif trigger_id == 'config_cancel_button':                                                              # pylint: disable=no-else-return
            updated_theme_children = []
            for child in current_themes_children_set:
                if (
                        isinstance(child, dict) and
                        'props' in child and
                        child['props'].get('id', {}).get('theme_card_added') is False
                ):
                    continue  # Skip this card (i.e., remove it)
                updated_theme_children.append(child)

            update_device_children = []
            for child in current_devices_children_set:
                if (
                        isinstance(child, dict) and
                        'props' in child and
                        child['props'].get('id', {}).get('device_added') is False
                ):
                    continue  # Skip this card (i.e., remove it)
                update_device_children.append(child)

            return False, 0, updated_theme_children, 0, update_device_children

        else:
            print(f"open_model function trigger unknown: {trigger_id}")
            raise PreventUpdate


    @app.callback(
        Output("nari_settings", "data"),
        Input("config_save_button", "n_clicks"),
        [
            # Devices tab
            State({"type": "device_instance_name", "device_id": ALL}, "value"),
            State({"type": "device_address", "device_id": ALL}, "value"),
            State({"type": "device_master_sync", "device_id": ALL}, "value"),
            State({"type": "device_active_status", "device_id": ALL}, "value"),

            # Themes tab
            State({"type": "theme_name_input", "theme_id": ALL}, "value"),
            State({"type": "theme_device_preset_selection", "theme_id": ALL, "device_id": ALL}, "value"),

            # General Settings tab
            State({"type": "input_general_settings", "name": ALL}, "value"),
            State({"type": "general_settings_row_meta", "name": ALL}, "data"),

            # Existing config (optional, fallback)
            State("nari_settings", "data"),
        ],
        prevent_initial_call=True
    )
    def save_config( n_clicks, device_instance_names, device_addresses, device_master_syncs, device_actives, theme_names,   # pylint: disable=too-many-arguments, too-many-positional-arguments
                     theme_preset_values, ui_setting_values, ui_setting_metas, existing_config) -> NariSettingsConfig:
        """ Handles the saving and updating of the Config file of current settings. """

        if not n_clicks:
            raise PreventUpdate

        current_config = {
            "devices": format_device_settings_export(callback_state=ctx.states_list),
            "themes": format_theme_settings_export(callback_state=ctx.states_list),
            "ui_settings": format_ui_settings_export(
                callback_state=ctx.states_list,
                existing_ui_settings=existing_config['ui_settings']
                )
        }

        save_configer(current_config)

        return current_config



def format_device_settings_export(callback_state: list[list[dict]]) -> list[DeviceConfig]:
    """ Builds the Device settings output for the config file. """
    device_name_entries = collect_states_by_type(
        callback_state=callback_state,
        component_type="device_instance_name",
        key_id_1="device_id"
    )

    device_address_entries = collect_states_by_type(
        callback_state=callback_state,
        component_type="device_address",
        key_id_1="device_id"
    )

    device_master_sync_entries = collect_states_by_type(
        callback_state=callback_state,
        component_type="device_master_sync",
        key_id_1="device_id"
    )

    device_active_entries = collect_states_by_type(
        callback_state=callback_state,
        component_type="device_active_status",
        key_id_1="device_id"
    )

    devices_dict = {}
    for device_id, value in device_name_entries:
        devices_dict.setdefault(int(device_id), {})["instance_name"] = value
    for device_id, value in device_address_entries:
        devices_dict.setdefault(int(device_id), {})["address"] = value
    for device_id, value in device_master_sync_entries:
        devices_dict.setdefault(int(device_id), {})["master_sync"] = bool(value)
    for device_id, value in device_active_entries:
        devices_dict.setdefault(int(device_id), {})["active"] = bool(value)

    devices_list = []
    for device_id, device_info in sorted(devices_dict.items(), key=lambda kv: kv[0]):
        devices_list.append(
            {
                "id": int(device_id),
                "address": device_info.get("address", "42.42.42.42"),  # TODO: need to put in a check
                "instance_name": device_info.get("instance_name", ""),  # TODO: Need to put in a check
                "master_sync": bool(device_info.get("master_sync")),  # Switch will always be True/False
                "active": bool(device_info.get("active")),  # Switch will always be True/False
            }
        )

    return devices_list


def format_theme_settings_export(callback_state: list[list[dict]]) -> list[ThemeSelectionConfig]:
    """ Builds the Theme settings output for the config file. """

    theme_set_name = collect_states_by_type(
        callback_state=callback_state,
        component_type="theme_name_input",
        key_id_1="theme_id"
    )

    theme_device_preset = collect_states_by_type(
        callback_state=callback_state,
        component_type="theme_device_preset_selection",
        key_id_1="theme_id",
        key_id_2="device_id"
    )

    theme_dict = {}
    for theme_id, value in theme_set_name:
        theme_dict.setdefault(int(theme_id), {})["name"] = value

    theme_device_preset_dict = {}
    for theme_id, device_id, preset_name in theme_device_preset:
        theme_device_preset_dict.setdefault(int(theme_id), []).append(
            {
                'device_id': device_id,
                'preset_name': preset_name
            }
        )

    themes_list = []
    for theme_id, theme_name in sorted(theme_set_name, key=lambda kv: kv[0]):
        themes_list.append(
            {
                "id": theme_id,
                "name": theme_name,
                "presets": theme_device_preset_dict.get(theme_id, []),
            }
        )

    return themes_list


def format_ui_settings_export(callback_state: list[list[dict]], existing_ui_settings: UISettings) -> UISettings:
    """ Builds the General settings output for the config file. """

    general_settings_name = collect_states_by_type(
        callback_state=callback_state,
        component_type="input_general_settings",
        key_id_1="name"
    )
    general_settings_dict = {}
    for setting_name, value in general_settings_name:
        general_settings_dict[setting_name] = {
            "value": value,
            "type": existing_ui_settings[setting_name]['type']
        }
    return general_settings_dict


def collect_states_by_type(callback_state: list[list[dict]], component_type: str, key_id_1: str, key_id_2: str = None):
    """ Converts the pulled State from the callback_context and pulls neccesary widget info. """
    collected = []
    for state in callback_state:
        if not isinstance(state, list):
            continue
        for state_entry in state:
            component_id = state_entry.get("id") or {}
            if isinstance(component_id, dict) and component_id.get("type") == component_type and state_entry.get("property") == "value" :
                if not key_id_2:
                    collected.append((component_id.get(key_id_1), state_entry.get("value")))
                else:
                    collected.append((component_id.get(key_id_1), component_id.get(key_id_2), state_entry.get("value")))
    return collected
