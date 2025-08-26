"""
Handles dynamic UI refreshes in response to app setting changes.

This includes the following functionalities:
    - Rebuilding layout content based on updated settings
    - Updating theme-related UI elements
    - Reflecting changes made through the Config Modal
"""

from __future__ import annotations

from dash import Input, Output

from nari_app.ui_parts.main_content import main_content
from nari_app.modals.config_modal import config_modal
from nari_app.util.config_builder import NariSettingsConfig


def layout_refresh_callbacks(app):
    """
        Register callbacks that refresh UI sections based on updated settings.

        Includes:
            - Rebuilding layout content
            - Updating theme-related dropdowns or containers
            - Reflecting changes made in the Config Modal
    """
    @app.callback(
        [
            Output('room-theme-mode', 'options'),
            Output('app_main_content', 'children'),
            Output('config_modal_container', 'children')
        ],
        Input('nari_settings', 'data'),
    )
    def ui_updated(nari_settings: NariSettingsConfig):
        """
           Rebuild UI sections when `nari_settings` changes. Normally after Config Save.
        """
        themes = nari_settings.get('themes', [])
        theme_options = [{'label': theme['name'], 'value': theme['id']} for theme in themes]

        return theme_options, main_content(nari_settings['devices']), config_modal(nari_settings)
