import dash.exceptions
from dash import Input, Output, State, html, ALL, callback_context, MATCH

from nari_app.modals.settings_modal import device_info_row


def global_settings_callback(app):

    @app.callback(
        Output('master_sync_device', 'disabled'),
        Input('update_master_sync_toggle', 'value')
    )

    def update_master_device(value):
        if value:
            return False
        return True

    @app.callback(
        [
            Output({'type': 'device_name', 'device_name': MATCH}, 'readonly'),
            Output({'type': 'device_ip_address', 'device_name': MATCH}, 'readonly'),
            Output({'type': 'device_instance_name', 'device_name': MATCH}, 'readonly')
        ],
        Input({'type': 'device_info_row_edit_button', 'device_name': MATCH},'value')
    )
    def edit_device_row(edit_button):
        if edit_button:
            return False, False, False
        return True, True, True


    @app.callback(
        Output('device_info_container', 'children'),
        [
            Input('add_device', 'n_clicks'),
            Input({'type': 'device_info_row_remove_button', 'device_name': ALL}, 'n_clicks')
        ],
        [
            State('device_info_container', 'children'),
            State("elements_initialized", 'data')
        ]
    )
    def add_device_row(add_button_click, remove_device_button_row, current_children_set, elements_initialized):
        ctx = callback_context

        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        triggered = ctx.triggered_id

        if elements_initialized:
            if triggered == 'add_device':
                new_device = {
                    'name':f"device_{add_button_click}",
                    'address': f"666.666.666.666",
                    'instance_name': f"Something Unholy"
                }

                new_device_row = device_info_row(new_device)

                render_set = current_children_set + [new_device_row]

                return render_set

            elif isinstance(triggered, dict) and triggered['type'] == 'device_info_row_remove_button':
                row_to_remove = triggered['device_name']

                update_children = []
                for child in current_children_set:
                    if (
                            isinstance(child, dict) and
                            'props' in child and
                            child['props'].get('id', {}).get('type') == 'settings_device_info_row' and
                            child['props']['id'].get('device_name') == row_to_remove
                    ):
                        continue  # Skip this card (i.e., remove it)
                    update_children.append(child)

                return update_children

        return current_children_set