"""
Handles callbacks that control individual WLED devices.

This includes interactions that target one or more explicitly defined devices,
such as applying presets, adjusting brightness, or sending specific POST commands.

These controls are scoped to single devices or device groups—distinct from global
actions that affect the entire system.
"""

from concurrent.futures import ThreadPoolExecutor
import os
import logging

from dotenv import load_dotenv
import dash.exceptions
from dash import Input, Output, State, ALL, ctx
from dash.exceptions import PreventUpdate

from naari_logging.naari_logger import LogManager
from naari_app.util.config_builder import DeviceConfig, UISettings
from naari_app.util.send_payload import  send_preset, brightness_adjustment, PayloadRetryError
from naari_app.util.util_functions import get_device

__all__ = ['device_controls_callbacks']

MAINDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ",,"))
load_dotenv(os.path.join(MAINDIR, ".env"))
TO_LOG = int(os.getenv("LOGGING", "0")) == 1


def device_controls_callbacks(app):     # pylint: disable=too-many-statements
    """
       Register callbacks for controlling individual WLED devices.

       Includes:
           - Applying presets to specific devices
           - Adjusting brightness per device via slider or automation
           - Updating indicators or local state based on per-device changes

       All callbacks in this module are scoped to individual device control,
       not global actions across all devices.
    """

    @app.callback(
        Output({'type': "brightness_slider", 'device_id': ALL}, "value"),
        [
            Input('brightness_chain_trigger', 'n_clicks'),
            Input({'type': 'preset_selection', 'device_id': ALL}, 'value'),
        ],
        [
            State('auto_mode', 'data'),
            State('device_catch_data', 'data'),
            State('devices_catch_presets', 'data'),
            State('naari_settings', 'data'),
            State('elements_initialized', 'data')
        ]
    )
    def brightness_preset_setter(brightness_chain_trigger, preset_option, is_auto_mode, polled_cach_data,      #pylint: disable=too-many-locals, too-many-branches, too-many-arguments, too-many-positional-arguments
                                 cached_presets, naari_settings, elements_initialized):
        """
            The selected preset will perform the following actions
            1) will adjust the Brightness slider widget according to current polled device data
            2) if preset is selected, will adjust the brightness widget accordingly and send a 'POST' call to the device chanigng to selected preset.
        """
        if not ctx.triggered_id or not elements_initialized:
            raise PreventUpdate

        # Build baseline: device_id -> current brightness from polled data
        try:
            devices_brightness = {
                device['device_id']: device.get('data', 0).get('state', {}).get('bri', 0)
                for device in polled_cach_data
            }
        except TypeError:
            # polled_device data has an issue or malformed
            LogManager.print_message(
                "Brightness setter issue. polled_device data has an issue or malformed",
                to_log=TO_LOG,
                log_level=logging.ERROR
            )
            raise PreventUpdate     # pylint: disable=raise-missing-from

        # Use the UI-rendered order for preset dropdowns to map ids -> values robustly
        # inputs_list[1] corresponds to the second Input group: preset_selection 'value'
        preset_inputs_group_order = dash.ctx.inputs_list[1]
        widget_ordered_preset_ids = [
            item['id']['device_id']
            for item in preset_inputs_group_order
            if isinstance(item.get('id'), dict) and item.get('property') == 'value'
        ]

        if isinstance(ctx.triggered_id, dict) and ctx.triggered_id['type'] == 'preset_selection':
            submissions = {}  # device_id -> (preset_id:int, device_info)

            if is_auto_mode:
                # Preset set to for UI as a str ex -> "2: Work"
                preset_values = [parse_preset_id(preset) for preset in preset_option]
                widget_preset_mapping = dict(zip(widget_ordered_preset_ids, preset_values))

                for dev_id, preset_id_str in widget_preset_mapping.items():
                    if preset_id_str not in (None, "", "0"):
                        device_info = get_device(devices=naari_settings['devices'], device_id=dev_id)
                        submissions[dev_id] = (int(preset_id_str), device_info)

                devices_brightness = {
                    device_id: get_brightness(device_id, preset, cached_presets)
                    for device_id, preset in widget_preset_mapping.items()
                }

            else:  # User selects specific 'Card' preset widget.
                triggered_info = ctx.triggered[0]  # {'prop_id': '...', 'value': '<id: name>'}
                triggered_device_id = ctx.triggered_id['device_id']
                preset_value = parse_preset_id(triggered_info.get('value'))

                selected_device = get_device(
                    device_id=triggered_device_id,
                    devices=naari_settings['devices']
                )

                # For sending POST bellow
                if preset_value not in (None, "", 0):
                    submissions[triggered_device_id] = (int(preset_value), selected_device)

                # Note: preset_value must be str
                changed_brightness = next(
                    (data['data'].get(preset_value, {}).get('bri')
                     for data in cached_presets if data['device_id'] == triggered_device_id),
                    None
                )
                if changed_brightness is not None:
                    devices_brightness[triggered_device_id] = changed_brightness

            # Send presets only *after* app is loaded
            # Utilizing Threading to best simulate all lights triggering at once
            # Only utilizing 4 threads due to lower strain on Pi
            if submissions:
                with ThreadPoolExecutor(max_workers=4) as executor:
                    for preset_value, target_device in submissions.values():
                        executor.submit(
                            _preset_sender,
                            preset_value,
                            target_device,
                            naari_settings['ui_settings']
                        )

        values_out = []
        for item in preset_inputs_group_order:
            if isinstance(item.get('id'), dict) and item.get('property') == 'value':
                device_id = item['id']['device_id']
                values_out.append(devices_brightness.get(device_id, 0))

        return values_out

    @app.callback(
        [
            Output('auto_mode', 'data', allow_duplicate=True),
            Output({'type': 'brightness_indicator', 'device_id': ALL}, 'children'),
            Output('init_brightness_chain_trigger', 'data', allow_duplicate=True),
            Output('reset_poll_interval', 'data', allow_duplicate=True)
        ],
        Input({'type': "brightness_slider", 'device_id': ALL}, "value"),
        [
            State('auto_mode', 'data'),
            State("naari_settings", 'data'),
            State('init_brightness_chain_trigger', 'data')
        ],
        prevent_initial_call=True
    )
    def handle_brightness_changes(brightness_values, auto_mode, naari_settings, brightness_chain_trigger):
        """
            Mirror slider values into the brightness indicators;
            if user-driven and auto mode is off, send a brightness update to the targeted device.
        """
        if not ctx.triggered:
            raise PreventUpdate

        # Prevents turning devices on/off during initial page loading.
        if brightness_chain_trigger:
            return False, list(brightness_values), False, False

        # Only when manipulated manually by user
        if not auto_mode:
            target_device_id = ctx.triggered_id['device_id']
            target_device = get_device(
                devices=naari_settings['devices'],
                device_id=target_device_id
            )

            # Build a mapping of device_id -> slider_value from the current input group
            # Easier extraction?
            input_group = ctx.inputs_list[0]  # Only input in Callback
            widget_value_map = {ui_widget['id'].get('device_id'): ui_widget['value'] for ui_widget in input_group}
            changed_value = widget_value_map.get(target_device_id, None)

            if changed_value is not None:
                try:
                    brightness_adjustment(
                        change_value=changed_value,
                        device_info=target_device,
                        ui_settings=naari_settings["ui_settings"]
                    )
                except PayloadRetryError as err:
                    # TODO: add trigger indicating what device had an error?
                    LogManager.print_message(
                        "Brightness update failed after %s attempts (url=%s): %s",
                        getattr(err, 'attempts', 'n/a'),
                        getattr(err, 'url', 'n/a'),
                        getattr(err, 'last_exception', err),
                        to_log=TO_LOG,
                        log_level=logging.ERROR
                    )

                except Exception as exc:        # pylint: disable=broad-exception-caught
                    # TODO: Make popup?
                    LogManager.print_message(
                        "Unexpected error updating device_id %s: %s",
                        target_device_id, exc,
                        to_log=TO_LOG,
                        log_level=logging.ERROR
                    )

        return False, list(brightness_values), False, True


#----------------------------------- helper functions-----------------------#
def _preset_sender(preset_value: int, target_device: DeviceConfig, ui_settings: UISettings):
    send_preset(
        preset_value=preset_value,
        device_info=target_device,
        ui_settings=ui_settings
    )

def parse_preset_id(preset: str):
    if not preset:
        return None
    return preset.split(":")[0].strip()

def get_brightness(selected_device, preset_value, presets_data):
    return next((device['data'][preset_value].get('bri', None) for device in presets_data if device['device_id'] == selected_device), 0)
