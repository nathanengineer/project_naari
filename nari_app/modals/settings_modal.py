import json

import dash_bootstrap_components as dbc
from dash import html


def _mater_device_name(devices: list[dict], selected_device: dict):
    return dbc.Select(
        id='master_sync_device',
        options=[
            {
                "label": device['instance_name'],
                'value': json.dumps(device)     # value must be a string or serialized json string
            }
            for device in devices
        ],
        value=[json.dumps(device) for device in devices if device['instance_name'] == selected_device['instance_name']][0],
        disabled=True,
        class_name='w-50'
    )

def _update_master_device_name():
    return dbc.Switch(
        id='update_master_sync_toggle',
        value=False
    )

def _update_device_info_toggle(device_name):
    return dbc.Switch(
        id={'type': 'device_info_row_edit_button', 'device_name': device_name},
        value=False
    )

def _remove_device_row(device_name):
    return dbc.Button(
        id={'type': 'device_info_row_remove_button', 'device_name': device_name},
        color='primary',
        class_name='',
        size='sm',
        children=[
            html.I(className="bi bi-trash fs-5")
        ]
    )

def _device_col_label():
    return dbc.Row(
        [
            dbc.Col(width=1),
            dbc.Col(html.Span("Device Name", className='mx-auto text-center'), width=3, class_name='d-flex align-items-center'),
            dbc.Col(html.Span("Device Address", className='mx-auto text-center'), width=3, class_name='d-flex align-items-center'),
            dbc.Col(html.Span("Instance Name", className='mx-auto text-center'), width=3, class_name='d-flex align-items-center'),
            dbc.Col(width=2)
        ]
    )

def _add_device_row_button():
    return dbc.Row(
        class_name='',
        children=[
            dbc.Col(),
            dbc.Col(
                width=6,
                class_name='',
                children=dbc.Button(
                    id='add_device',
                    color='primary',
                    children='Add Device',
                    class_name='w-100'
                )
            ),
            dbc.Col()
        ]
    )

def device_info_row(device: dict):
    return dbc.Row(
        id={'type': 'settings_device_info_row', 'device_name': device['name']},
        class_name='p-1',
        children=[
            dbc.Col(
                width=1,
                class_name='d-flex align-items-center',
                children=dbc.Label(
                    f"Device:",
                    class_name='d-flex align-items-center'
                )
            ),
            dbc.Col(
                width=3,
                children=[
                    dbc.Input(
                        id={'type': 'device_name', 'device_name': device['name']},
                        value=device['name'],
                        placeholder="Name Of Device",
                        readonly=True
                    ),
                    dbc.Tooltip(
                        "Enter name for the Device. Ex: big lights",
                        target={'type': 'device_name', 'device_name': device['name']},
                        placement="top"
                    )
                ]

            ),
            dbc.Col(
                width=3,
                children=[
                    dbc.Input(
                    id={'type': 'device_ip_address', 'device_name': device['name']},
                    value=device['address'],
                    readonly=True
                    ),
                    dbc.Tooltip(
                        "Enter the DNS/IP address for the Device. Ex: 111.111.111",
                        target={'type': 'device_ip_address', 'device_name': device['name']},
                        placement="top"
                    )
                ]
            ),
            dbc.Col(
                width=3,
                children=[
                    dbc.Input(
                        id={'type': 'device_instance_name', 'device_name': device['name']},
                        value=device['instance_name'],
                        readonly=True
                    ),
                    dbc.Tooltip(
                        "Enter what will be display name for the Device. Ex: BIG LIGHTS YAH!",
                        target={'type': 'device_instance_name', 'device_name': device['name']},
                        placement="top"
                    )
                ]
            ),
            dbc.Col(
                children=[
                    dbc.Stack(
                        direction='horizontal',
                        gap=2,
                        children=[
                            _update_device_info_toggle(device['name']),
                            _remove_device_row(device['name'])
                        ]
                    )
                ]
            )
        ]
    )


def _device_info_container(nari_settings):
    return html.Div(
        id='device_info_container',
        children=[
            *[device_info_row(device) for device in nari_settings['devices']]
        ]
    )

def master_sync_device(nari_settings):
    return dbc.Row(
        id = 'mater_sync_device_row',
        class_name='',
        children= [
            dbc.Col(
                width=3,
                children=dbc.Label("Master Sync Device", class_name='fs-6')
            ),
            dbc.Col(
                dbc.Stack(
                    direction='horizontal',
                    gap=3,
                    children=[
                        _mater_device_name(nari_settings['devices'], nari_settings['master_device']),
                        _update_master_device_name()
                    ]
                )
            )
        ]
    )

def _polling_input(polling_value):
    return dbc.Input(
        id='polling_input',
        value=polling_value,
        disabled=True,
        class_name='w-25',
        type='number',
    )

def _polling_input_edit_switch():
    return dbc.Switch(
        id='polling_edit_switch',
        value=False
    )

def polling_settings(polling_settings):
    return dbc.Row(
        id='polling_settings_row',
        class_name='',
        children=[
            dbc.Col(
                width=3,
                children=dbc.Label("Polling Setting (s):", class_name='fs-6')
            ),
            dbc.Col(
                dbc.Stack(
                    direction='horizontal',
                    gap=3,
                    children=[
                        _polling_input(polling_settings),
                        _polling_input_edit_switch()
                    ]
                )
            )
        ]
    )

def nari_setting_info(nari_settings):
    return dbc.Container(
        id="nari_settings_container",
        fluid=True,
        class_name='',
        children= [
            dbc.Row([], class_name='my-3'),
            dbc.Row(
                class_name='d-flex justify-content-center',
                children=html.H5('Nari_Settings', className='d-flex justify-content-center')
            ),
            dbc.Row([], class_name='my-1'),
            polling_settings(nari_settings['ui_settings']['polling_rate']),
            dbc.Row([], class_name='my-1'),
            master_sync_device(nari_settings),
            dbc.Row([], class_name='my-3'),
            dbc.Row(
                class_name='d-flex justify-content-center',
                children=html.H5('Current Network Devices', className='d-flex justify-content-center')
            ),
            dbc.Row([], class_name='my-1'),
            _device_col_label(),
            _device_info_container(nari_settings),
            dbc.Row([], class_name='my-1'),
            _add_device_row_button()
        ]
    )