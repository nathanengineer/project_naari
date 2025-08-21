import dash_bootstrap_components as dbc
from dash import html, dcc

from nari_app.util.config_builder import DeviceConfig

# Notes for color usage:
# - Primary   -> Active / Working
# - Secondary -> Inactive / Not functional

def _power_button(device_name: str) -> dbc.Button:
    """Per-device power toggle (secondary until actual state is known)."""
    return dbc.Button(
        [
            html.I(className="bi bi-power fs-5"),
        ],
        id={'type': 'power_button', 'device': device_name},
        color="secondary",
        className="d-flex justify-content-center align-items-center",
        size="md"
    )


def _brightness_slider(device_name: str) -> dcc.Slider:
    """ Per-device brightness slider; limit set to 0–255. """
    return dcc.Slider(
        id={'type': 'brightness_slider', 'device': device_name},
        min=0,
        max=255,
        step=1,
        marks=None,
        value=None,         # set by callbacks when data arrives
        updatemode='drag',
        className='m-0 p-0'
    )


def _brightness_indicator(device_name: str) -> html.Span:
    """ Text indicator displaying current brightness value. """
    return html.Span(
            id={'type': 'brightness_indicator', 'device': device_name},
            className='fs-5',
            children=None
    )


def _preset_selections(device_name: str) -> dbc.Select:
    """ Device preset dropdown; options populated by callbacks. """
    return dbc.Select(
        id={'type': 'preset_selection', 'device': device_name},
        options=[],             # filled by callbacks
        style={'width': '100%'},
        className='d-flex justify-content-center align-items-center'
    )


def _collapse_button(device_name: str) -> dbc.Button:
    """ Button to toggle the extra device details collapse. """
    return dbc.Button(
        id={'type': 'device_collapse_button', 'device': device_name},
        color='primary',
        class_name='',
        size='sm',
        n_clicks=1,     # 1 odd = 'is_open' = False and 2 even = 'is_open' = True
        children=[
            html.I(className="bi bi-plus fs-5")     # TODO: change from plut to arrows?
        ]
    )


def _collapse_element(device_name: str) -> dbc.Collapse:
    """ Collapsed area reserved for future per-device extra/additional controls/details. """
    return dbc.Collapse(
            id={'type': 'collapse_segment', 'device': device_name},
            is_open=False,      # must match the initial n_click logic above
            children=[
                dbc.Card(dbc.CardBody("Reserve Space for more stuff"))
            ]
        )


def _device_row(device_name: str):
    """ Single row of controls for a device address/name key. """
    return dbc.Row(
        children=[
            dbc.Col(
                children=[
                    _power_button(device_name),
                    # Stores used by callbacks for state/control chaining
                    dcc.Store(id={'type': 'power_on', 'device': device_name}, data=None)
                ],
                xs=1,
                md=1,
                class_name=' d-flex justify-content-center align-items-center'
            ),
            dbc.Col(
                children=[
                    _preset_selections(device_name),
                    dcc.Store(id={'type': 'preset_selection_interaction_meta', 'device': device_name}, data=False)
                ],
                xs=3,
                md=3,
                class_name=' d-flex justify-content-center align-items-center'
            ),
            dbc.Col(
                xs=7, md=7,
                class_name='mt-2 justify-content-center align-items-center',
                children=[
                    dbc.Stack(
                        direction='horizontal',
                        children=[
                            html.Div(
                                children=[
                                    _brightness_slider(device_name),
                                    dcc.Store(id={'type': 'brightness_slider_chain_meta', 'device': device_name}, data=False),
                                    dcc.Store(id={'type': 'brightness_slider_manual_update', 'device': device_name}, data=False)
                                ],
                                className='w-100'
                            ),
                            html.Div([], className='p-1'),
                            html.Div(
                                children=[
                                    _brightness_indicator(device_name),
                                    dcc.Store(id={'type': 'brightness_indicator_interaction_meta', 'device': device_name}, data=False)
                                ],
                                className='d-flex justify-content-center align-items-center'
                            )
                        ]
                    )
                ]
            ),
            dbc.Col(_collapse_button(device_name), xs=1, md=1, class_name=' d-flex justify-content-center align-items-center'),
            # hidden dummy per-device output for chaining assistance
            html.Div(id={'type': 'dummy_output', 'device': device_name}, style={'display': "none"})
        ]
    )

def _device_frame(device: DeviceConfig) -> dbc.Card:
    """ Card wrapper per device with title, controls row, and the collapse area. """
    return dbc.Card(
        body=True,
        children=[
            html.H6(f"{device['instance_name'].replace('_', ' ').title()}"),
            _device_row(device['address']),
            _collapse_element(device['address']),
            dcc.Store(id={'type': 'card_interaction_meta', 'device': device['address']}, data=False)
        ]
    )


def main_content(system_devices: list[DeviceConfig]) -> dbc.Container:
    """ Assemble the main content: one card per device (layout only; data via callbacks). """
    return dbc.Container(
        fluid=True,
        children=[
            dbc.Row([], class_name='my-2'),
            dbc.Stack(
                class_name='',
                gap=4,
                children=[
                    *[_device_frame(device) for device in system_devices]
                ]
            )
        ]
    )