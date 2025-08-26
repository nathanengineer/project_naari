""" Modular that handles the Callbacks of the Device Tab of the Config Modal. """

import dash.exceptions
from dash import html, Input, Output, State, ALL, ctx, MATCH

from nari_app.modals.device_tab import device_card      # pylint: disable=import-error

# TODO: move this into master call class?
COLLAPSE_OPEN_SYMBOL = html.I(className="bi bi-caret-left-fill fs-5")
COLLAPSE_CLOSE_SYMBOL = html.I(className="bi bi-caret-down-fill fs-5")


def device_settings_callback(app):
    """
        Register all Dash callbacks that power the Device Settings tab.

        This function wires the backend logic for device configuration,
        including adding, updating, and removing devices.
    """
    #TODO: add element_inizialise prevension, is needed?
    @app.callback(
        [
            Output({'type': 'device_collapse_element', 'device_id': MATCH}, 'is_open'),
            Output({'type': 'device_collapse_button', 'device_id': MATCH}, 'children'),
            Output({'type': 'device_instance_name', 'device_id': MATCH}, 'readonly'),
            Output({'type': 'device_address', 'device_id': MATCH}, 'readonly')
        ],
        Input({'type': 'device_collapse_button', 'device_id': MATCH}, 'n_clicks'),

    )
    def view_device_settings(button):
        """Toggle the device card collapse view and editability of its fields."""

        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        # Collapse logic: odd clicks → open, even clicks → closed
        collapse_is_open = not bool(button % 2)

        card_name_readonly = card_address_readonly = bool(button % 2)

        button_image = COLLAPSE_CLOSE_SYMBOL if button % 2 else COLLAPSE_OPEN_SYMBOL

        return  collapse_is_open, button_image, card_name_readonly, card_address_readonly


    @app.callback(
        Output({'type': 'device_master_sync', 'device_id': ALL}, 'value'),
        Input({'type': 'device_master_sync', 'device_id': ALL}, 'value'),
    )
    def master_sync_device_switch(_):
        """ Ensures only one device is selected as the Master Sync """
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        triggered_device_id  = ctx.triggered_id ['device_id']

        # Resets all False
        device_state_map  = {card['id']['device_id']: False for card in ctx.inputs_list[0]}

        # Assigns only one device based off what device 'ID' got triggered
        device_state_map[triggered_device_id ] = True

        return list(device_state_map.values())


    @app.callback(
        Output('devices_stack', 'children', allow_duplicate=True),
        [
            Input('device_add_button', 'n_clicks'),
            Input({'type': 'device_remove_button', 'device_id': ALL}, 'n_clicks')
        ],
        [
            State('devices_stack', 'children'),
            State('nari_settings', 'data'),
        ],
    )
    def add_remove_device_card(add_mode_click, remove_mode_clicks, current_children_set, nari_settings):    # pylint: disable=unused-argument

        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        triggered = ctx.triggered_id


        if triggered == 'device_add_button' and add_mode_click:     # pylint: disable=no-else-return

            # Collect existing device IDs from config and performce a safe additoin if nothing in config file.
            device_ids = (device["id"] for device in nari_settings['devices'])
            next_id = (max(device_ids) + 1) if device_ids else 1        # pylint: disable=using-constant-test

            # Setup the dictionary that will be sent
            new_device = {
                'id': next_id,
                'address': "42.42.42.42",
                'instance_name': "Answer to Everything",
                'master_sync': False,
                'active': True
            }

            # Creates the Layout that will be Rendered to the current list
            new_card = device_card(
                device_info=new_device,
                init_loaded=False
            )

            # Safely appends the new card into the set
            render_set = current_children_set + [new_card]

            return render_set

        elif isinstance(triggered, dict) and triggered['type'] == 'device_remove_button':    # pylint disable=no-else-return
            device_to_remove = triggered['device_id']

            updated_children = []
            # Shifts through to find card being removed.
            for child in current_children_set:

                if (
                        isinstance(child, dict) and
                        'props' in child and
                        child['props'].get('id', {}).get('type') == 'device_card_settings' and
                        child['props'].get('id', {}).get('device_id') == device_to_remove
                ):
                    continue  # Skip this card (i.e., remove it)
                updated_children.append(child)

            return updated_children

        return current_children_set
