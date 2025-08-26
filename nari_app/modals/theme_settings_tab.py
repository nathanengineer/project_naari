""" Modular contains the font end layout and widgets of the Tab portion called Theme Modes Tab. """

import dash_bootstrap_components as dbc
from dash import html

from nari_app.util.config_builder import DeviceConfig, ThemeSelectionConfig, DevicePreset

__all__ = [
    'theme_card',
    'theme_tab_container'
]


def _delete_theme(theme_id: int) -> dbc.Button:
    """ Basic Button Widget. Goal to remove paired theme card. """
    return dbc.Button(
        id={'type': 'theme_delete', 'theme_id': theme_id},
        color='primary',
        size='sm',
        children=[
            html.I(className="bi bi-trash fs-5")
        ]
    )


def _theme_name_input(theme_id: int, theme_name: str) -> dbc.Input:
    """ Basic Input Widget. Goal is to label paired theme. """
    return dbc.Input(
        id={'type': 'theme_name_input', 'theme_id': theme_id},
        value=theme_name.title(),
        readonly=True
    )


def _edit_card_switch(theme_id, readonly: bool) -> dbc.Switch:
    """ Basic Switch Widget. Ensure user edit intent. """
    return dbc.Switch(
        id={'type': 'theme_name_edit', 'theme_id': theme_id},
        value=readonly
    )


def _collapse_theme_button(theme_id: int) -> dbc.Button:
    """ Basic Button Widget. Gaol is to pair collapsable widget underneath the paired card. """
    return dbc.Button(
        id={'type': 'theme_card_collapse_button', 'theme_id': theme_id},
        color='primary',
        size='sm',
        n_clicks=1,  # 1 odd = 'is_open' = False and 2 even = 'is_open' = True
        children=[
            html.I(className="bi bi-caret-down-fill fs-5")
        ]
    )


def _collapse_theme_elements(theme_id: int, presets: list[DevicePreset], devices: list[DeviceConfig]):
    """ Widget paired with the card underneath the card row. Hiding other settings. Keeping the UI clean. """
    def _theme_device_preset_selections(device_id: int, preset_name: str, is_active: bool) -> dbc.Select:
        """
            Combo box of the device polled presets.
            On initial page load, is set to config settings, for saving and Dash shortcomings. Thanks, Dash!
        """
        return dbc.Select(
            id={'type': 'theme_device_preset_selection', 'theme_id': theme_id, 'device_id': device_id},
            options=[],     # gets filled in from Callback after polling device for preset
            value=preset_name,
            style={'width': '100%'},
            className='d-flex justify-content-center align-items-center',
            disabled= not is_active    # if not active disables
        )


    def _theme_card_device_row(device: DeviceConfig) -> dbc.Row:
        """ Row of device and polled presets. """
        # Pulls what is the preset_name in config file per device.
        config_preset_value = next((value['preset_name'] for value in presets if value['device_id'] == device['id']), "")

        return dbc.Row(
            id={'type': 'theme_device_preset', 'theme_id': theme_id, 'device_id': device['id']},
            children=[
                dbc.Col( children=html.Span(device.get("instance_name", "")) ),         # Label
                # Create row per device in config
                dbc.Col( children=_theme_device_preset_selections(
                    device['id'],
                    config_preset_value.title(),
                    device['active']
                ))     # Combobox
            ]
        )

    return dbc.Collapse(
        id={'type': 'theme_collapse_element', 'theme_id': theme_id},
        is_open=False,      # Hides unnecessary info and keeps UI clean. False = Hide/No
        children=[
            dbc.Row([], class_name='my-2'),
            *[ _theme_card_device_row(device) for device in devices ]
        ]
    )


def _theme_add_button() -> dbc.Button:
    """ Basie Button Widget. Goal to add new Theme Card. """
    return dbc.Button(
        id='theme_add_button',
        color='primary',
        class_name='w-50',
        size='sm',
        children='Add / Insert'
    )


def theme_card(theme_info: ThemeSelectionConfig, devices: list[DeviceConfig], readonly: bool, init_load: bool) -> dbc.Card:
    """ Builds the different Themes as Dash Cards. """
    return dbc.Card(
        id={'type': 'theme_card', 'theme_id': theme_info['id'], 'theme_card_added': init_load},
        body=True,
        children=[
            dbc.Row(
                children=[
                    dbc.Col(
                        width=5,
                        class_name='align-middle',
                        children=[
                            dbc.Stack(
                                direction='horizontal',
                                gap=4,
                                children=[
                                    _delete_theme(theme_info['id']),        # Delete Button
                                    _theme_name_input(                      # Theme Name Widget
                                        theme_id=theme_info['id'],
                                        theme_name=theme_info['name']
                                    ),
                                    _edit_card_switch(theme_info['id'], readonly)   # Edit Name Widget
                                ]
                            )
                        ]
                    ),
                    dbc.Col(
                        width=7,
                        class_name='d-flex justify-content-end',
                        children=_collapse_theme_button(theme_info['id'])       # Collapse Button
                    )
                ]
            ),
            _collapse_theme_elements(                                   # Hidden/Show device presets + selections
                theme_id=theme_info['id'],
                presets=theme_info['presets'],
                devices=devices
            )
        ]
    )


def theme_tab_container(theme_list: list[ThemeSelectionConfig], devices: list[DeviceConfig]) -> dbc.Container:
    """ HOlds the Theme Cards dictated by the config file. """
    return dbc.Container(
        id="theme_tab_container",
        fluid=True,             # Aids when user opens up site on any platform
        children=[
            dbc.Row([], class_name='my-2'),
            dbc.Stack(
                id='theme_cards_stack',
                gap=3,
                children=[
                    *[theme_card(theme_info=theme, devices=devices, readonly=False, init_load=True) for theme in theme_list]
                ]
            ),
            dbc.Row([], class_name='my-2'),
            html.Div(
                className='d-flex justify-content-center',
                children=_theme_add_button()
            )
        ]
    )
