""" Modular contains the font end layout and widgets of the Tab portion called Device Tab. """

import dash_bootstrap_components as dbc
from dash import html

from naari_app.util.config_builder import DeviceConfig

__all__ = [
    'device_card',
    'device_tab_container'
]

def _remove_device(device_id: int) -> dbc.Button:
    """ Basic Button Widget. Goal to remove paired device card. """
    return dbc.Button(
        id={'type': 'device_remove_button', 'device_id': device_id},
        color='primary',
        class_name='',
        size='sm',
        children=[
            html.I(className="bi bi-trash fs-5")
        ]
    )


def _card_name(device_id: int, device_instance_name: str) -> dbc.Input:
    """ Basic Input Widget. Goal is to label paired device. """
    return dbc.Input(
        id={'type': 'device_instance_name', 'device_id': device_id},
        value=device_instance_name.title(),
        readonly=True
    )


def _device_address_field(device_id: int, device_address: str) -> dbc.Input:
    """ Basic Input Widget. Goal is to add IP address to device. """
    return dbc.Input(
        id={'type': 'device_address', 'device_id': device_id},
        value=device_address,
        readonly=True
    )


def _device_master_sync_box(device_id: int, sync_value: bool) -> dbc.Switch:
    """
        Basic Switch Widget. \
        Goal is to tell UI that this paired device is the Master device.
        True = Yes, False = No.
    """
    return dbc.Switch(
        id={'type': 'device_master_sync', 'device_id': device_id},
        value=sync_value
    )


def _device_active_switch(device_id: int, active_value: bool) -> dbc.Switch:
    """
        Basic Switch Widget.
        Goal is to tell UI that this specific device is currently active in the ego system.
        True = Yes, False = No
    """
    return dbc.Switch(
        id={'type': 'device_active_status', 'device_id': device_id},
        value=active_value
    )


def _collapse_mode_button(device_id: int) -> dbc.Button:
    """ Basic Button Widget. Gaol is to pair collapsable widget underneath the paired card. """
    return dbc.Button(
        id={'type': 'device_collapse_button', 'device_id': device_id},
        color='primary',
        size='sm',
        n_clicks=1,  # 1 odd = 'is_open' = False and 2 even = 'is_open' = True
        children=[
            html.I(className="bi bi-caret-down-fill fs-5")
        ]
    )


def _collapse_mode_elements(device_info: DeviceConfig) -> dbc.Collapse:
    """ Widget paired with the card underneath the card row. """
    return dbc.Collapse(
        id={'type': 'device_collapse_element', 'device_id': device_info['id']},
        is_open=False,      # Initially close to not overwhelm UI and visually.
        children=[
            dbc.Row([], class_name='my-2'),
            dbc.Row(
                children=[
                    dbc.Col(
                        width=2,
                        class_name='d-flex justify-content-center',
                        children=_remove_device(device_id=device_info['id']),
                    ),
                    dbc.Col(
                        width = 5,
                        children=[
                            dbc.Stack(
                                direction='horizontal',
                                gap=3,
                                class_name='d-flex justify-content-center pt-2',
                                children=[
                                    dbc.Label("Master Sync Device:"),
                                    _device_master_sync_box(
                                        device_id=device_info['id'],
                                        sync_value=device_info['master_sync']
                                    )
                                ]
                            )
                        ]
                    ),
                    dbc.Col(
                        width = 5,
                        children=[
                            dbc.Stack(
                                direction='horizontal',
                                gap=3,
                                class_name='d-flex justify-content-center pt-2',
                                children=[
                                    dbc.Label("Active Device:"),
                                    _device_active_switch(
                                        device_id=device_info['id'],
                                        active_value=device_info['active']
                                    )
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    )


def _device_add_button() -> dbc.Button:
    """ Basic Button Widget. Goal is to add a new device card. """
    return dbc.Button(
        id='device_add_button',
        color='primary',
        class_name='w-50',
        size='sm',
        children='Add / Insert'
    )


def device_card(device_info: DeviceConfig, init_loaded: bool) -> dbc.Card:
    """
    Builds the different Dash Cards displaying the different Devices and its settings.
    Current Settings:
         'address', 'instance_name', 'master_sync', 'active'
    """
    return dbc.Card(
        id={'type': 'device_card_settings', 'device_id': device_info['id'], 'device_added': init_loaded },
        body=True,
        children=[
            dbc.Row(
                children=[
                    dbc.Col(
                        width=1,
                        class_name='pt-2',
                        children=dbc.Label("Device:")
                    ),
                    dbc.Col(
                        width=3,
                        children=_card_name(
                            device_id=device_info['id'],
                            device_instance_name=device_info['instance_name']
                        )
                    ),
                    dbc.Col(
                        width=3,
                        class_name='d-flex justify-content-end pt-2',
                        children=dbc.Label("Device Address:", class_name='text-end')
                    ),
                    dbc.Col(
                        width=4,
                        children=_device_address_field(
                            device_id=device_info['id'],
                            device_address=device_info['address']
                        )
                    ),
                    dbc.Col(
                        width=1,
                        children=_collapse_mode_button(device_id=device_info['id'],)
                    ),
                ]
            ),
            _collapse_mode_elements(device_info)
        ]
    )


def device_tab_container(devices: list[DeviceConfig]) -> dbc.Container:
    """ HOlds the Device Cards dictated by the config file. """
    return dbc.Container(
        id="device_tab_container",
        fluid=True,                 # aids when user opens up site on any platform
        children=[
            dbc.Row([], class_name='my-2'),
            dbc.Stack(
                id='devices_stack',
                gap=3,
                children=[ *[device_card(devices, True) for devices in devices] ]
            ),
            dbc.Row([], class_name='my-2'),
            html.Div(
                className='d-flex justify-content-center',
                children=_device_add_button()
            )
        ]
    )
