"""
Handles global WLED control callbacks that apply system-wide.

These callbacks issue POST commands that affect all devices or a designated group through global triggers like theme changes or master on/off switches.
"""

import dash.exceptions
from dash import Input, Output, State, ALL, ctx
from dash.exceptions import PreventUpdate


from nari_app.util.send_payload import  send_payload
from nari_app.util.util_functions import is_app_loaded, get_master_device


BUTTON_INDICATOR = {
    True: "success",    #Onn
    False: "danger",    #Off
    None: 'secondary'   #Error
}

def global_controls_callback(app):
    """
       Register callbacks for controlling all WLED devices simultaneously.

       Includes:
           - Applying themes that trigger preset changes across all devices
           - Toggling power state via the master power button

       These callbacks apply system-wide logic and affect multiple devices at once.
    """
    @app.callback(
        [
            Output('auto_mode', 'data', allow_duplicate=True),
            Output({'type': 'preset_selection', 'device_id': ALL}, 'value')
        ],
        Input('room-theme-mode', 'value'),
        [
            State({'type': 'preset_selection', 'device_id': ALL}, 'options'),
            State('nari_settings', 'data'),
            State('elements_initialized', 'data')
        ],
    )
    def mode_change(selected_theme_id, _preset_options, nari_settings, elements_initialized):
        """
            When the room theme changes, enable auto mode and set each device's preset dropdown
            to the theme-defined preset. Returns [True, <list of preset names aligned to UI order>].

            Note: Auto_mode starts here
        """
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        if elements_initialized is False:
            raise PreventUpdate

        themes = nari_settings.get('themes', [])
        theme = next((theme for theme in themes if theme.get('id') == int(selected_theme_id)), None)
        if not theme:
            raise PreventUpdate

        presets_for_theme = theme.get('presets', [])
        preset_by_device_id = {preset.get('device_id'): preset.get('preset_name') for preset in presets_for_theme}

        # ctx.states_list[0] corresponds to State({'type': 'preset_selection', ...}, 'options')
        state_group = ctx.states_list[0]
        device_options_by_widget_device_id = {
            item['id'].get('device_id'): item['value']
            for item in state_group
            if isinstance(item.get('id'), dict) and item.get('property') == 'options'
        }

        # Build values list aligned to UI order (None if theme lacks a preset)
        # Also checks if config preset is in combobox dropdown.
        new_dropdown_values = []
        for device_id, options in device_options_by_widget_device_id.items():
            desired = preset_by_device_id.get(device_id)  # /d: Name
            new_dropdown_values.append(desired if desired in options else "")  # Options: list of /d: Name

        return True, new_dropdown_values


    @app.callback(
        Output('master-power-btn', 'color'),
        Input('master-power-btn', 'n_clicks'),
        [
            State("device_catch_data", 'data'),
            State('nari_settings', 'data'),
            State("elements_initialized", 'data')
        ]
    )
    @is_app_loaded()
    def master_power_button(_, polled_devices, nari_settings, elements_initialized):    # pylint: disable=too-many-return-statements
        """
            Handle clicks on the Master Power button.

            - Finds the master device from settings
            - Reads its current state from cached device data
            - Sends a payload to toggle power on click
            - Returns a color representing current/failed state
        """
        if elements_initialized is False or not ctx.triggered_id:
            raise PreventUpdate

        master_device = get_master_device(nari_settings.get('devices'))
        if not master_device:
            return 'danger'  # TODO: Work on pupop window for this error.

        udpn_enabled = next((device.get('data', None).get('state').get('udpn').get('send') for device in polled_devices if device['ip'] == master_device['address']), None)
        if udpn_enabled is None:
            return 'danger'  # TODO: need popup window for this error.

        is_power_on = next((device['data']['state']["on"] for device in polled_devices if device['ip'] == master_device['address']))

        if not ctx.triggered_id == 'master-power-btn':
            if is_power_on:
                return "primary"  # Devices On
            return 'secondary'  # Devices Off

        # Toggle target power state
        # Not using API function call because intent is to use Master Sync device
        system_power_on = not is_power_on       # Changes state
        power_payload = {"on": system_power_on}
        api_response = send_payload(master_device["address"], power_payload)

        if api_response.status_code == 200 and is_power_on:     # pylint: disable=no-else-return
            return 'primary'  # Devices On
        elif api_response.status_code == 200 and not is_power_on:
            return 'secondary'  # Devices Off
        else:
            return 'danger'  # Issues on response
