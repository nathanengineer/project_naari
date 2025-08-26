"""UI Sidebar for N.A.R.I Control Panel.

Contains:
- Master controls (power, info, refresh, config)
- Mode selection dropdown
- Master brightness slider
"""

import dash_bootstrap_components as dbc
from dash import html, dcc

from nari_app.util.config_builder import ThemeSelectionConfig

__all__=['sidebar']

# Notes for color usage:
# - Primary   -> Active / Working
# - Secondary -> Inactive / Not functional
# - Danger    -> Danger / Critical

#----------------Button Functions--------------------#

def _master_power_button() -> dbc.Button:
    """ Primary power toggle for all devices. """
    return dbc.Button(
        title='Power',
        id="master-power-btn",
        color="primary",
        class_name="d-flex justify-content-center align-items-center mb-2 w-auto",
        children=[
            html.I(className="bi bi-power fs-5"),
            html.Span(
                " Power",
                className="ms-2"
            )
        ])


def _config_button() -> dbc.Button:
    """ Opens the configuration modal. """
    return  dbc.Button(
        id="config-btn",
        color="primary",
        n_clicks=0,
        className="d-flex justify-content-center align-items-center mb-2 w-auto",
        children=[
            html.I(className="bi bi-gear fs-5"),
            html.Span(
                " Config",
                className="ms-2"
            )
        ]
)

def _info_button() -> dbc.Button:
    """ Currently disabled info/help button. """
    return dbc.Button(
        id='master_info_button',
        color='secondary',
        className="d-flex justify-content-center align-items-center mb-2",
        children=[
            html.I(className="bi bi-info-square fs-5"),
            html.Span(
                "Info",
                className="ms-2"
            )
        ],
        disabled=True
    )

def _refresh_button() -> dbc.Button:
    """ Reloads in Data and Presets from all connected devices, populates UI """
    return dbc.Button(
        id='refresh_button',
        color='primary',
        className="d-flex justify-content-center align-items-center mb-2",
        children=[
            html.I(className="bi bi-arrow-repeat fs-5"),
            html.Span(
                " Refresh",
                className="ms-2"
            )
        ]
    )


def _button_stack() -> dbc.Stack:
    """ Container for the main control buttons. """
    return dbc.Stack(
        class_name='mx-1',
        direction='vertical',
        gap=1,
        children=[
            _master_power_button(),
            _info_button(),
            _refresh_button(),
            _config_button()
        ]
    )


#-------------------Theme Selection Functions----------------------#

def _theme_dropdown(themes: list[ThemeSelectionConfig]) -> dbc.Select:
    """ Dropdown for selecting room theme/mode. """
    return dbc.Select(
        id='room-theme-mode',
        options=[ {'label': theme['name'], 'value': theme['id']} if theme['id'] else "" for theme in themes ],
        value="",
        className="align-item-middle",
        style={"width": "auto"}
    )

def _master_brightness_slider() -> dcc.Slider:
    """ Slider for controlling master brightness across devices. """
    return dcc.Slider(
        id='master-brightness-slider',
        min=0,
        max=255,
        step=1,
        marks=None,
        value=128,
        updatemode='drag',
        tooltip={"placement": "bottom", "always_visible": True},
        className='g-0'
    )



def _mode_selection_stack(theme_selections: list[ThemeSelectionConfig]) -> dbc.Stack:
    """" Container for Theme selection widgets. """
    return dbc.Stack(
        class_name='mx-1',
        direction='vertical',
        gap=1,
        children=[
            html.Div(
                html.Span("Theme Selection"),
                className='d-flex align-items-center justify-content-center'),
            _theme_dropdown(theme_selections)
        ]
    )

def _brightness_stack() -> dbc.Stack:
    """ Container for Master Brightness widgets. """
    return dbc.Stack(
        direction='vertical',
        children=[
            html.Div(
                html.Span("Master Brightness"),
                className='mx-1 d-flex align-items-center justify-content-center'),
            _master_brightness_slider()
        ]
    )


#-------------------------Primary Container Function--------------------------------#

def sidebar(theme_selections: list[ThemeSelectionConfig]) -> dbc.Container:
    """ Constructs the sidebar UI containing global controls and theme sections."""
    return dbc.Container(
        fluid=True,
        className='mx-auto',
        children=[
            dbc.Row([], class_name='my-2'),
            dbc.Row(_button_stack()),
            dbc.Row([], class_name='my-2'),
            dbc.Row(
                children=_mode_selection_stack(theme_selections)
            ),
            dbc.Row([], class_name='my-3'),
            dbc.Row(
                html.Div(
                    html.Span("Master Brightness"),
                    className='mx-1 d-flex align-items-center justify-content-center'
                )
            ),
            dbc.Row(_master_brightness_slider()),

            html.Br(),

            dbc.Row(children=[
                # AI Assistant placeholder
                html.Div(
                    style={"textAlign": "center"},
                    children=[
                        html.Img(
                            src="/static/img/assistant_placeholder.png",
                            style={"width": "100%", "marginBottom": "0.5rem"}
                        ),
                        html.P(
                            "AI Assistant coming soon…",
                               className="text-muted small"
                        )
                ])
            ])
    ])
