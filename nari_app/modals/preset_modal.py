import dash_bootstrap_components as dbc
from dash import html


def _mode_card_preset_selections(device_name, mode_name):
    return dbc.Select(
        id={'type': 'mode_card_preset_selection', 'device': device_name, 'mode_name': mode_name},
        options=[],
        style={'width': '100%'},
        className='d-flex justify-content-center align-items-center'
    )

def _mode_card_preset_row(device_name, mode_name):
    return dbc.Row(
        id={'type': 'mode_card_preset_row', 'device': device_name, 'mode_name': mode_name},
        class_name='',
        children=[
            dbc.Col(
                class_name='',
                children=html.Span(device_name),
            ),
            dbc.Col(
                class_name='',
                children=_mode_card_preset_selections(device_name, mode_name)
            )
        ]
    )


def _collapse_mode_elements(mode_preset):
    return dbc.Collapse(
        id={'type': 'mode_card_collapse_element', 'mode_name': mode_preset['name']},
        is_open=False,
        children=[
            dbc.Row([], class_name='my-2'),
            *[_mode_card_preset_row(device['device_address'], mode_preset['name']) for device in mode_preset['presets']]
        ]
    )

def _card_name(name: str):
    return dbc.Input(
        id={'type': 'mode_card_name_element', 'mode_name': name},
        value=name.title(),
        readonly=True
    )

def _edit_card_name(name: str, readonly: bool):
    return dbc.Switch(
        id={'type': 'mode_card_name_edit_element', 'mode_name': name},
        value=readonly
    )

def _remove_card_button(name):
    return dbc.Button(
        id={'type': 'remove_card_element', 'mode_name': name},
        color='primary',
        class_name='',
        size='sm',
        children=[
            html.I(className="bi bi-trash fs-5")
        ]
    )


def _collapse_mode_button(mode_preset_name: str):
    return dbc.Button(
        id={'type': 'mode_card_collapse_button', 'mode_name': mode_preset_name},
        color='primary',
        class_name='',
        size='sm',
        n_clicks=1,  # 1 odd = 'is_open' = False and 2 even = 'is_open' = True
        children=[
            html.I(className="bi bi-caret-down-fill fs-5")
        ]
    )


def mode_card(mode_preset: dict, readonly: bool):
    return dbc.Card(
        id={'type': 'mode_card', 'mode_name': mode_preset['name']},
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
                                gap=3,
                                children=[
                                    _remove_card_button(mode_preset['name']),
                                    _card_name(
                                        name=mode_preset['name']
                                    ),
                                    _edit_card_name(mode_preset['name'], readonly)
                                ]
                            )
                        ]
                    ),
                    dbc.Col(
                        width=7,
                        class_name='d-flex justify-content-end',
                        children=_collapse_mode_button(mode_preset['name'])
                    )
                ]
            ),
            _collapse_mode_elements(mode_preset)
        ]
    )


def preset_mode_add_button():
    return dbc.Button(
        id='preset_mode_add_button',
        color='primary',
        class_name='w-50',
        size='sm',
        children='Add / Insert'
    )
