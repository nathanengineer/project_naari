import time
from concurrent.futures import ThreadPoolExecutor

import dash.exceptions
from dash import Input, Output, State, ALL, callback_context
from dash.exceptions import PreventUpdate

from nari_app.util.wled_device_status import get_devices_ip, poll_all_devices, poll_device_presets
from nari_app.util.send_payload import send_device_power_update, send_preset, brightness_adjustment, send_payload
from nari_app.util.util_functions import is_app_loaded


BUTTON_INDICATOR = {
    True: "success",    #Onn
    False: "danger",    #Off
    None: 'secondary'   #Error
}


def status_callbacks(app):

    @app.callback(
        Output('device_catch_data', 'data'),
        Input('poll-interval', 'n_intervals'),
        State('nari_settings', 'data')
    )
    # TODO: see if there a way I can send a notification or make a UI change if an error occures.
    def poll_devices(_, nari_settings):
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        if ctx.triggered_id == 'poll-interval':
            ip_list = get_devices_ip(nari_settings)
            catch_data = poll_all_devices(device_address_list= ip_list)
            if catch_data and all('data' in device for device in catch_data):
                return catch_data
            # TODO: Logg here
            print("error in polling for data")
            return catch_data
        return PreventUpdate


    @app.callback(
        [
            Output({'type': 'preset_selection', 'device': ALL}, 'options'),
            Output('devices_catch_presets', 'data'),
            Output("refresh_popup", 'is_open'),
            Output('refresh_popup', 'color'),
            Output('refresh_popup', 'children')
        ],
        [
            Input('data_app_load_check', 'data'),
            Input('refresh_button', 'n_clicks')
        ],
        [
            State("devices_catch_presets", "data"),
            State('nari_settings', 'data')
        ]
    )
    # TODO: Improvements? Highlight mismatches or defualt sets on errors?
    def preset_population(app_load_check, presets_refresh, polled_preset_data, nari_settings):
        ctx = callback_context

        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        popup_open = False
        popup_message = ""
        popup_color = 'secondary'

        if app_load_check and ctx.triggered_id == 'refresh_button':
            polled_preset_data = poll_device_presets(device_address_list = get_devices_ip(nari_settings))
            time.sleep(1)
            popup_message = "Presets Re-Loaded"
            popup_open = True
            popup_color = 'success'
            if not all('data' in device for device in polled_preset_data):
                # TODO: Pop up error here.
                popup_message = "Presets Failed to Re-Load"
                popup_color = 'danger'

        preset_options = [device_preset_list(device_preset) for device_preset in polled_preset_data]

        return preset_options, polled_preset_data, popup_open, popup_color, popup_message

    @app.callback(
        Output({'type': "brightness_slider", 'device': ALL}, "value"),
        [
            Input('data_app_load_check', 'data'),
            Input({'type': 'preset_selection', 'device': ALL}, 'value'),
            Input('refresh_button', 'n_clicks')
        ],
        [
            State('auto_mode', 'data'),
            State('device_catch_data', 'data'),
            State('devices_catch_presets', 'data'),
            State('nari_settings', 'data'),
            State("elements_initialized", 'data')
        ]
    )
    def brightness_preset_setter(page_load_check, presets, refresh_button, auto_mode, catch_data,
        presets_data, nari_settings, elements_initialized):

        ctx = callback_context

        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        # Build initial brightness mapping
        try:
            devices_brightness = {
                device['ip']: device.get('data', {}).get('state', {}).get('bri', 0)
                for device in catch_data
            }
        except TypeError:
            raise PreventUpdate

        if elements_initialized and isinstance(ctx.triggered_id, dict) and ctx.triggered_id['type'] == 'preset_selection':
            # Populate
            preset_submission = {}

            if auto_mode:

                preset_values = [p.split(":")[0] if p else None for p in presets]
                preset_submission = dict(zip(devices_brightness.keys(), preset_values))

                devices_brightness = {
                    device: get_brightness(device, preset, presets_data, devices_brightness)
                    for device, preset in preset_submission.items()
                }

            else:
                triggered_info = ctx.triggered[0]
                preset_value = triggered_info['value'].split(":")[0]
                selected_device = ctx.triggered_id['device']

                preset_submission[selected_device] = preset_value

                changed_brightness = next(
                    (d['data'].get(preset_value, {}).get('bri')
                     for d in presets_data if d['ip'] == selected_device),
                    None
                )
                if changed_brightness is not None:
                    devices_brightness[selected_device] = changed_brightness

            # Send presets only *after* app is loaded
            # Utilizing Threading to best simulate all lights triggering at once
            # Only utilizing 4 threads due to lower strain on Pi
            with ThreadPoolExecutor(max_workers=4) as executor:
                for device_ip, preset_value in preset_submission.items():
                    if preset_value not in (None, "", 0):
                        executor.submit(_preset_sender, device_ip, preset_value, nari_settings['master_device'])

        return list(devices_brightness.values())


    @app.callback(
        [
            Output('auto_off_switch_trigger', 'n_clicks'),
            Output({'type': 'brightness_indicator', 'device': ALL}, 'children')
        ],
        Input({'type': "brightness_slider", 'device': ALL}, "value"),
        [
            State('auto_mode', 'data'),
            State("device_catch_data", 'data'),
            State("nari_settings", 'data'),
            State('elements_initialized', 'data')
        ],
    )
    def brightness_update(values, auto_mode, cach_data, nari_settings, elements_initialized):

        if not callback_context.triggered:
            raise dash.exceptions.PreventUpdate

        if not elements_initialized:
            return 1, list(values)

        if not auto_mode and callback_context.triggered_id != 'refresh_button':
            device_name = callback_context.triggered_id['device']
            device_ids = [device['ip'] for device in cach_data]
            value_map = dict(zip(device_ids, values))
            changed_value = value_map.get(device_name, None)

            if changed_value is not None:
                brightness_adjustment(
                    change_value=changed_value,
                    ip_target=device_name,
                    sync_device_info=nari_settings['master_device']
                )

        return 1, list(values)


    # Automode initialized here
    @app.callback(
        [
            Output('auto_mode', 'data', allow_duplicate=True),
            Output({'type': 'preset_selection', 'device': ALL}, 'value')
        ],
        Input('room-theme-mode', 'value'),
        [
            State({'type': 'preset_selection', 'device': ALL}, 'options'),
            State('nari_settings', 'data'),
            State('elements_initialized', 'data')
        ],
    )
    #@is_app_loaded()
    def mode_change(theme, preset_options, nari_settings: dict, elements_initialized):
        ctx = callback_context

        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        if elements_initialized is False:
            raise PreventUpdate

        # preset_selection should be the first one
        # This is preset_options variable, just that I want the dictionary.
        preset_state_data = ctx.states_list[0]

        preset_names = [mode['presets'] for mode in nari_settings['modes'] if mode['name'] == theme][0]

        preset_option_data = [{preset_option['id']['device']: preset_option['value']} for preset_option in preset_state_data]

        preset_dropdown_change = get_preset_value(
            mode_selection=preset_names,
            widget_options_list=preset_option_data
        )

        return True, list(preset_dropdown_change.values())
    

    @app.callback(
        Output('auto_mode', 'data', allow_duplicate=True),
        Input('auto_off_switch_trigger', 'n_clicks')
    )
    def auto_off(clicks):
        return False


    @app.callback(
        Output({'type': 'power_button', 'device': ALL}, 'color'),
        [
            Input('data_app_load_check', 'data'),
            Input("device_catch_data", "data"),
            Input({'type': 'power_button', 'device': ALL}, 'n_clicks')
        ],
        [
            State("device_catch_data", "data"),
            State('nari_settings', 'data'),
        ]

    )
    def device_button_status(page_load_check, polled_data, button_click, cached_data, nari_settings):

        # Nothing polled yet? Don’t render.
        if not cached_data or not isinstance(cached_data, list):
            #TODO: add logger here
            raise PreventUpdate

        ctx = callback_context

        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        triggered_id = ctx.triggered_id

        # Determine what triggered the callback and which dataset to use

        # Hopefully Human Manual Intervention
        if isinstance(triggered_id, dict) and triggered_id['type'] == 'power_button':
            device_data = cached_data
            update_device = triggered_id.get('device') if isinstance(triggered_id, dict) else None
        # Initial Load
        elif triggered_id == 'data_app_load_check':
            device_data = cached_data
            update_device = None
        # Recurring Polling
        elif triggered_id == 'device_catch_data':
            device_data = polled_data
            update_device = None
        else:
            raise dash.exceptions.PreventUpdate

        # Safely extract on/off state
        indicator_status = {
            item.get("ip", "unknown"): (
                (item.get("data") or {}).get("state", {}).get("on")
                if isinstance(item.get("data"), dict) else None
            )
            for item in device_data
        }

        try:
            # If power button was clicked, toggle its state and send update
            if update_device and indicator_status[update_device] is not None:
                new_state = not indicator_status[update_device]
                send_device_power_update(
                    status_update=new_state,
                    ip_target=update_device,
                    sync_device_info=nari_settings['master_device']
                )
                indicator_status[update_device] = new_state

            # Map boolean states to button colors
            return [BUTTON_INDICATOR[state] for state in indicator_status.values()]

        except Exception as e:
            print(f"Error in update_power_button_colors: {e}")
            raise dash.exceptions.PreventUpdate


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
    def master_power_button(n_clicks, data, nari_settings, elements_initialized):
        if elements_initialized is False:
            raise PreventUpdate

        # First need to find the Master Sync device

        master_device_ip = nari_settings['master_device']['address']

        # TODO: Work on pupop window for resetting.
        sync_state = [device.get('data', None).get('state').get('udpn').get('send') for device in data if device['ip'] == master_device_ip][0]
        if sync_state is None:
            return 'danger'

        current_on_state = [device['data']['state']["on"] for device in data if device['ip'] == master_device_ip][0]

        if n_clicks:
            update_state = True
            if current_on_state:
                update_state = False

            payload = {"on": update_state}

            response = send_payload(master_device_ip, payload)

            if response.status_code == 200 and update_state:
                return 'primary'
            elif response.status_code == 200 and not update_state:
                return 'secondary'
            else:
                return 'danger'
        if current_on_state:
            return "primary"
        return 'secondary'




############################################################################################################################
################ Functions Bellow


# TODO: move to Util? using in config as well
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


def get_brightness(selected_device, preset_value, presets_data, current_brightness):
    if preset_value and len(preset_value):
        return [device['data'][preset_value].get('bri', None) for device in presets_data if device['ip'] == selected_device][0]

    # If preset value is empty returns previous set value
    return current_brightness[selected_device]


def get_preset_value(mode_selection: list[dict], widget_options_list: list[dict]):
    widget_updates = {}

    for selection in mode_selection:
        device = selection['device_address']
        preset_name = selection['preset_name']

        # Find matching widget options for the current device
        matching_options = next(
            (options[device] for options in widget_options_list if device in options),
            []
        )

        # Find dropdown value by matching preset_name
        # Formate -> #: Preset Name
        dropdown_value = next(
            (preset for preset in matching_options if preset_name == preset),
            ""
        )

        widget_updates[device] = dropdown_value

    return widget_updates


def _preset_sender(device_ip, preset_value, sync_device_info):
    send_preset(
        preset_value=preset_value,
        ip_target=device_ip,
        sync_device_info=sync_device_info
    )