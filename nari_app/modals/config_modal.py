""" Configuration modals: container and tabs for NARI settings. """

import dash_bootstrap_components as dbc
from dash import html

from nari_app.util.config_builder import NariSettingsConfig, ThemeSelectionConfig, UISettings
from nari_app.modals.preset_modal import mode_card, preset_mode_add_button
from nari_app.modals.settings_modal import nari_setting_info


def _save_button():
    """ Modal UI element associated with saving current entries in the modal. """
    return dbc.Button(
        children="Save",
        id='config_save_button',
        n_clicks=0,
        color='secondary',
        disabled=False
    )

def _cancel_button():
    """ Modal UI element, to exit/close/dismiss with out saving """
    return dbc.Button(
        children='Cancel',
        id='config_cancel_button',
        n_clicks=0
    )

# TODO: Should the main children get moved to 'theme_modal.py'
def _theme_mode_tab(themes: list[dict]):
    """ Container for the different Themes currently setup on NARI"""
    return dbc.Tab(
        id='_preset_mode_tab',  # TODO: need to change this to 'theme_mode_tab'
        label='Theme Modes',
        children=[
            dbc.Row([], class_name='my-2'),
            dbc.Stack(
                id='preset_mode_card_stack',    # Todo: need to change this to 'theme_mode_card_stack'
                class_name='',
                gap=2,
                children=[
                    *[mode_card(mode, False) for mode in themes if mode['name']]
                ]
            ),
            dbc.Row([], class_name='my-2'),
            html.Div(
                className='d-flex justify-content-center',
                children=preset_mode_add_button()
            )
        ]
    )

def _device_tab(nari_settings: dict):
    """ Holds the modual UI elements for Nari global settings like devices"""
    return dbc.Tab(
        id='_device_mode_tab',
        label='Devices Global Settings',
        children=[
            nari_setting_info(nari_settings)
        ]
    )

def _other_tab():
    return dbc.Tab(
        id='_other_tab',
        label='Other Something Settings',
        children=[]
    )


def config_modal(config_settings: dict):
    """ Tab container that stores the different components/sections of the NARI viewable configuration"""
    return dbc.Modal(
        id='modals',
        centered=True,
        is_open=False,
        size='lg',
        children=[
            dbc.ModalHeader(dbc.ModalTitle("N.A.R.I Configer"), close_button=False),
            dbc.ModalBody([
                dbc.Tabs([
                    _theme_mode_tab(config_settings['modes']),
                    _device_tab(config_settings),
                    _other_tab()
                ])
            ]),
            dbc.ModalFooter(
                children=[
                    _save_button(),
                    _cancel_button()
                ]
            ),
            html.Div(id='config_save_target_blank', children=[])
        ]
    )