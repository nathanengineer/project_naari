""" Configuration modals: container and tabs for NARI settings. """

import dash_bootstrap_components as dbc

from nari_app.util.config_builder import NariSettingsConfig, UISettings

from nari_app.modals.general_settings_tab import general_settings_container
from nari_app.modals.device_tab import device_tab_container
from nari_app.modals.theme_settings_tab import theme_tab_container

__all__ = ['config_modal']


def _theme_tab(nari_settings: NariSettingsConfig) -> dbc.Tab:
    """ Holds the different Themes widgets for the Model Config UI """
    return dbc.Tab(
        id = 'theme_tab',
        label="Theme Modes",
        children=theme_tab_container(
            theme_list=nari_settings['themes'],
            devices=nari_settings['devices']
        )
    )

def _device_tab(nari_settings: NariSettingsConfig):
    """ Holds the Devices For the ego system with in the Model Config UI """
    return dbc.Tab(
        id='_device_mode_tab',
        label='Devices Settings',
        children=device_tab_container(nari_settings['devices'])
    )


def _general_settings_tab(nari_settings: UISettings) -> dbc.Tab:
    """ Holds the the different settings of the backend of NARI. """
    return dbc.Tab(
        id='_other_tab',
        label='App General Settings',
        children=general_settings_container(nari_settings)
    )


def config_modal(config_settings: NariSettingsConfig) -> dbc.Modal:
    """ Tab container that stores the different components/sections of the NARI viewable configuration"""
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

    return dbc.Modal(
        id='config_modal',
        centered=True,
        is_open=False,
        size='lg',
        children=[
            dbc.ModalHeader(dbc.ModalTitle("N.A.R.I Configer"), close_button=False),
            dbc.ModalBody([
                dbc.Tabs([
                    _theme_tab(config_settings),
                    _device_tab(config_settings),
                    _general_settings_tab(config_settings['ui_settings'])
                ])
            ]),
            dbc.ModalFooter(
                children=[
                    _save_button(),
                    _cancel_button()
                ]
            )
        ]
    )
