"""
Handles global WLED control callbacks that apply system-wide.

These callbacks issue POST commands that affect all devices or a designated group through global triggers like theme changes or master on/off switches.
"""

import os
import logging

from dotenv import load_dotenv
import dash.exceptions
from dash import Input, Output, State, ALL, ctx
from dash.exceptions import PreventUpdate

from naari_logging.naari_logger import LogManager
from naari_app.util.send_payload import  send_payload
from naari_app.util.util_functions import get_master_device

MAINDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ",,"))
load_dotenv(os.path.join(MAINDIR, ".env"))
TO_LOG = int(os.getenv("LOGGING", "0")) == 1

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
            State('naari_settings', 'data'),
            State('elements_initialized', 'data')
        ],
    )
    def mode_change(selected_theme_id, _preset_options, naari_settings, elements_initialized):
        """
            When the room theme changes, enable auto mode and set each device's preset dropdown
            to the theme-defined preset. Returns [True, <list of preset names aligned to UI order>].

            Note: Auto_mode starts here
        """
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        if elements_initialized is False:
            raise PreventUpdate

        themes = naari_settings.get('themes', [])
        theme = next((theme for theme in themes if theme.get('id') == int(selected_theme_id)), None)
        if not theme:
            LogManager.print_message(
                "Theme not in Config. Check Settings",
                to_log=TO_LOG,
                log_level=logging.WARNING
            )
            # TODO: Popup issue
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
        [
            Output('master-power-btn', 'color'),
            Output('reset_poll_interval', 'data')
        ],
        [
            Input('master-power-btn', 'n_clicks'),
            Input('initial_device_catch_data', 'data')      # Aids in initial color value.
        ],
        [
            State("device_catch_data", 'data'),
            State('naari_settings', 'data'),
        ]
    )
    def master_power_button(_button_click, _initial_load, polled_devices, naari_settings):    # pylint: disable=too-many-return-statements
        """
            Handle clicks on the Master Power button.

            - Finds the master device from settings
            - Reads its current state from cached device data
            - Sends a payload to toggle power on click
            - Returns a color representing current/failed state
        """
        if not ctx.triggered_id:
            raise PreventUpdate

        master_device = get_master_device(naari_settings.get('devices'))
        if not master_device:
            return 'danger', False  # TODO: Work on pupop window for this error.

        udpn_enabled = next((device.get('data', None).get('state').get('udpn').get('send') for device in polled_devices if device['ip'] == master_device['address']), None)
        if udpn_enabled is None:
            return 'danger', False  # TODO: need popup window for this error.

        is_power_on = next((device['data']['state']["on"] for device in polled_devices if device['ip'] == master_device['address']))

        # Initial button color value
        if not ctx.triggered_id == 'master-power-btn':
            if is_power_on:
                return "primary", False  # Devices On
            return 'secondary', False  # Devices Off

        # Toggle target power state
        # Not using API function call because intent is to use Master Sync device
        system_power_on = not is_power_on       # Changes state
        power_payload = {"on": system_power_on}
        api_response = send_payload(master_device["address"], power_payload)

        if api_response.status_code == 200 and is_power_on:     # Devices Off   pylint: disable=no-else-return
            return 'secondary', True
        elif api_response.status_code == 200 and not is_power_on:   # Devices On
            return 'primary', True
        else:
            return 'danger', True  # Issues on response
