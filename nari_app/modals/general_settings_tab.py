""" Modular contains the font end layout and widgets of the Tab portion called General Settings Tab. """

import dash_bootstrap_components as dbc
from dash import dcc

from nari_app.util.config_builder import UISettings

__all__=['general_settings_container']

def _label_add_units(label_name) -> str:
    match label_name:
        case "polling_rate":
            units = " (sec)"
        case "connect_timeout":
            units = " (sec)"
        case "read_timeout":
            units = " (sec)"
        case "retry_backoff":
            units = " (sec)"
        case "request_timeout":
            units = " (sec)"
        case _:
            units = ""

    return f"{label_name.replace("_", " ").capitalize()}{units}:"


def _determine_type(data_type: str) -> str:
    match data_type:
        case "int" | "float":
            return 'number'
        case "str":
            return 'text'
        case _:
            return 'text'


def _general_settings(setting_name: str, data: dict) -> dbc.Row:
    """ Builds the different rows of settings predetermine in the config file. """
    def _input():
        """ Basic Input Widget. """
        return dbc.Input(
            id={'type': 'input_general_settings', "name": setting_name},
            value=data['value'],
            disabled=True,      # Ensure user does not unintentionally edited.
            class_name='w-25',
            type=_determine_type(data['type']),
        )

    def _edit_switch():
        """ Basic Switch Widget. Ensure user edit intent. """
        return dbc.Switch(
            id={'type': 'edit_general_input_switch', "name": setting_name},
            value=False         # Ensure user does not unintentionally edited.
        )

    def _label():
        """ basic Label widget. """
        return dbc.Label(
            id={'type': 'label_general_settings', "name": setting_name},
            class_name='fs-6',
            children=_label_add_units(label_name=setting_name)
        )

    return dbc.Row(
        id={'type': "general_settings_row", "name": setting_name},
        children=[
            dcc.Store(
                id={'type': "general_settings_row_meta", "name": setting_name},
                data=data,
            ),
            dbc.Col(
                width=3,
                children=_label()
            ),
            dbc.Col(
                dbc.Stack(
                    direction='horizontal',
                    gap=3,
                    children=[
                        _input(),
                        _edit_switch()
                    ]
                )
            ),
        ]
    )


def general_settings_container(nari_settings: UISettings) -> dbc.Container:
    """ HOlds the general setting widgets dictated by the config file. """
    return dbc.Container(
        id = "nari_general_settings_container",
        fluid=True,     # aids when user opens up site on any platform
        class_name='justify-content-center',
        children=[
            dbc.Row([], class_name='my-3'),
            dbc.Stack(
                direction="vertical",
                gap=3,
                class_name='d-flex justify-content-center',
                children= [
                    *[_general_settings(setting_name=key, data=value) for key, value in nari_settings.items()]
                ]

            )

        ]
    )
