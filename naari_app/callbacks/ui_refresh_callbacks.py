"""
Handles dynamic UI refreshes in response to app setting changes.

This includes the following functionalities:
    - Rendering/updating layout content
    - Updating theme-related dropdowns or containers
    - Reflecting changes made in the Config Modal when updated
"""

from __future__ import annotations

from dash import Input, Output

from naari_app.ui_parts.main_content import main_content
from naari_app.modals.config_modal import config_modal
from naari_app.util.config_builder import NaariSettingsConfig


def layout_refresh_callbacks(app):
    """
        Register callbacks that refresh UI sections based on updated settings.

        Includes:
            - Rendering/updating layout content
            - Updating theme-related dropdowns or containers
            - Reflecting changes made in the Config Modal when updated
    """
    @app.callback(
        [
            Output('room-theme-mode', 'options'),
            Output('app_main_content', 'children'),
            Output('config_modal_container', 'children'),
            Output('init_brightness_chain_trigger', 'data')
        ],
        Input('naari_settings', 'data'),
    )
    def ui_updated(naari_settings: NaariSettingsConfig):
        """
           Rebuild UI sections when `naari_settings` changes. Normally after Config Save.
        """
        themes = naari_settings.get('themes', [])
        theme_options = [{'label': theme['name'], 'value': theme['id']} for theme in themes if themes]

        return theme_options, main_content(naari_settings.get('devices', [])), config_modal(naari_settings), True
