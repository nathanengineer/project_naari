"""
Handles polling and device status update callbacks.

These callbacks collect data from WLED devices through GET requests and update the UI accordingly.
"""

import time

import dash.exceptions
from dash import Input, Output, State, ALL, ctx
from dash.exceptions import PreventUpdate

from naari_app.util.wled_device_status import get_devices_ip, poll_all_devices, poll_device_presets
from naari_app.util.send_payload import send_device_power_update, PayloadRetryError
from naari_app.util.util_functions import device_polled_data_mapping, is_device_active, get_device


BUTTON_INDICATOR = {
    True: "success",    #Onn
    False: "danger",    #Off
    None: 'secondary'   #Error
}


def status_callbacks(app):      # pylint: disable=too-many-statements
    """
       Register callbacks responsible for polling device data
       and updating UI status indicators.

       Includes:
           - Polling devices for /json and /presets.json data
           - Populating UI elements with current presets
           - Updating visual status of power buttons based on polled results
    """

    @app.callback(
        Output('device_catch_data', 'data'),
        Input('poll-interval', 'n_intervals'),
        State('naari_settings', 'data')
    )
    # TODO: see if there a way I can send a notification or make a UI change if an error occures.
    def poll_devices(_, naari_settings):
        if not ctx.triggered:
            raise PreventUpdate

        if ctx.triggered_id == 'poll-interval':

            ip_list = get_devices_ip(
                naari_devices=naari_settings.get('devices'),
                get_inactive=False
            )

            catch_data = device_polled_data_mapping(
                cach_data=poll_all_devices(device_address_list= ip_list),
                devices=naari_settings.get('devices')
            )
            if catch_data and all('data' in device for device in catch_data):
                return catch_data

            # TODO: Logg here
            print("error in polling for data")
            return catch_data
        return PreventUpdate


    @app.callback(
        [
            Output({'type': 'preset_selection', 'device_id': ALL}, 'options'),
            Output('devices_catch_presets', 'data'),
            Output("refresh_popup", 'is_open'),
            Output('refresh_popup', 'color'),
            Output('refresh_popup', 'children'),
            Output('brightness_chain_trigger', 'data')
        ],
        [
            Input('data_app_load_check', 'data'),
            Input('refresh_button', 'n_clicks')
        ],
        [
            State("devices_catch_presets", "data"),
            State('naari_settings', 'data')
        ],
        prevent_initial_call=True
    )
    # TODO: Improvements? Highlight mismatches or defualt sets on errors?
    def preset_population(_app_load_check, _presets_refresh, cached_preset_data, naari_settings):
        """ Populate preset dropdowns for active devices and refresh data when triggered. Shows a popup to indicate success or failure during refresh. """
        if not ctx.triggered:
            raise dash.exceptions.PreventUpdate

        popup_open = False
        popup_message = ""
        popup_color = 'secondary'

        if ctx.triggered_id == 'refresh_button':
            try:
                device_ips = get_devices_ip(naari_devices=naari_settings.get('devices'))
                cached_preset_data = device_polled_data_mapping(
                    cach_data=poll_device_presets(device_address_list = device_ips),
                    devices=naari_settings.get('devices')
                )
                time.sleep(1)   # to provide time for async polling to catch up if needed with UI.
                popup_message = "Presets Re-Loaded"
                popup_open = True
                popup_color = 'success'
                if not all('data' in device for device in cached_preset_data):
                    # TODO: Pop up error here.
                    popup_message = "Some presets failed to load"
                    popup_color = 'info'

            except Exception as e:
                # TODO: logging here
                #logger.exception("Preset refresh failed: %s", e)
                popup_open = True
                popup_color = 'danger'
                popup_message = "Preset refresh failed"

        active_devices_presets = [
            device_preset for device_preset in cached_preset_data
            if is_device_active(
                device_id=device_preset['device_id'],
                devices=naari_settings['devices']
            )
        ]
        options_per_device = [device_preset_list(device_preset) for device_preset in active_devices_presets]

        return options_per_device, cached_preset_data, popup_open, popup_color, popup_message, True


    @app.callback(
        Output({'type': 'power_button', 'device_id': ALL}, 'color'),
        [
            Input('data_app_load_check', 'data'),
            Input("device_catch_data", "data"),
            Input({'type': 'power_button', 'device_id': ALL}, 'n_clicks')
        ],
        [
            State("device_catch_data", "data"),
            State('naari_settings', 'data'),
            State('elements_initialized', 'data')
        ],
        prevent_initial_call=True,
    )
    def device_power_button_status(_page_load_check, polled_data, _button_click, cached_device_data, naari_settings, elements_initialized):
        """ Updates the Power Button widget color based on if device is on or off. """
        # Nothing polled yet? Don’t render.
        if not cached_device_data or not isinstance(cached_device_data, list):
            #TODO: add logger here
            raise PreventUpdate

        if not ctx.triggered:
            raise PreventUpdate

        if not elements_initialized:
            raise PreventUpdate

        triggered_id = ctx.triggered_id

        if isinstance(triggered_id, dict) and triggered_id['type'] == 'power_button':   # Button Click / Manual Entry
            devices_cach_data = cached_device_data
            target_device = get_device(
                devices=naari_settings['devices'],
                device_id=triggered_id['device_id']
            )
        elif triggered_id == 'data_app_load_check':     # Initial Loads
            devices_cach_data = cached_device_data
            target_device = None
        elif triggered_id == 'device_catch_data':       # For Poll-Intervals
            devices_cach_data = polled_data
            target_device = None
        else:
            raise dash.exceptions.PreventUpdate

        # UI order for power buttons (pattern-matched ALL group)
        # NOTE: ctx.inputs_list[2] corresponds to Input({'type': 'power_button'}, 'n_clicks')
        power_inputs_group = ctx.inputs_list[2]
        ui_devices_order = [
            ui_device['id'].get('device_id', 0) for ui_device in power_inputs_group
            if isinstance(ui_device['id'], dict)
            and ui_device['id'].get('type') == 'power_button'
        ]

        # Filtering only active running. Needed from page reload or initial App startup.
        # Note: Interval Polling devices will have only active data from active set devices
        active_ui_devices  = [
            data for data in devices_cach_data
            if is_device_active(
                device_id=data.get('device_id'),
                devices=naari_settings.get('devices')
            )
        ]

        # Safely extract on/off state
        # {device_id: True/False/None}
        indicator_status = {
            entry.get('device_id'): (
                entry.get('data', {}).get('state', {}).get('on')
                if isinstance(entry.get('data'), dict) else None
            )
            for entry in active_ui_devices
        }

        # If a button was clicked, toggle that device and update the map
        if target_device:
            target_id = target_device['id']
            if indicator_status[target_id] is not None:
                new_state = not indicator_status[target_id]
                try:
                    send_device_power_update(
                        status_update=new_state,
                        device_info=target_device,
                        ui_settings=naari_settings['ui_settings']
                    )
                    indicator_status[target_id] = new_state
                except PayloadRetryError as err:
                    # Keep previous state (color) and log rich context
                    #logger.error(
                    #    "Power toggle failed after %s attempts (url=%s): %s",
                    #    getattr(err, "attempts", "n/a"),
                    #    getattr(err, "url", "n/a"),
                    #    getattr(err, "last_exception", err),
                    #    exc_info=True
                    #)
                    # TODO: add trigger indicating what device had an error?
                    print(err)

                except Exception:
                    # Truly unexpected—log & keep previous state
                    #logger.exception("Unexpected error toggling device %s", target_id)
                    print("Unexpected error toggling device %s", target_id)     # TODO: Logging
                    # leave state_map[target_id] unchanged


        # Map in exact UI order; safe fallback when state missing/None
        power_buttons_color = [BUTTON_INDICATOR.get(indicator_status[device_id], 'secondary') for device_id in ui_devices_order]

        return power_buttons_color


#---------- Helper Functions------------------------#

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
