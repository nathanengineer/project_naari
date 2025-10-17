"""
Handles application configuration loading on page load.

This module registers callbacks that load the NAARI configuration
(`naari_config.json`) into the app's data store when the page first loads.
Once loaded, the other callbacks are triggered accordinlgy

"""

from __future__ import annotations

import logging
import time
import os

from dotenv import load_dotenv
from dash import Input, Output
from dash.exceptions import PreventUpdate

from naari_logging.naari_logger import LogManager
from naari_app.util.config_builder import NaariSettingsConfig
from naari_app.util.util_functions import naari_config_load

MAINDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ",,"))
load_dotenv(os.path.join(MAINDIR, ".env"))
TO_LOG = int(os.getenv("LOGGING", "0")) == 1


def startup_callbacks(app):
    """ Register startup callback for loading app configuration on page load."""

    @app.callback(
        [
            Output('naari_settings', 'data', allow_duplicate=True),
            Output('data_app_load_check', 'data',  allow_duplicate=True),

        ],
        Input('url', 'pathname'),
    )
    # TODO: see if there a way I can send a notification or make a UI change if an error occures.
    def page_data_load(_) -> tuple[NaariSettingsConfig, bool, bool]:
        """
            Triggered on initial page load or reload.

            Loads the NAARI configuration from `naari_config.json` and stores it
            in the app's main settings store. If the config fails to load,
            the app halts further initialization.
        """

        naari_settings = naari_config_load()
        time.sleep(1)

        if not naari_settings:
            LogManager.print_message(
                "Config File unable to load. Check system.",
                to_log=TO_LOG,
                log_level=logging.CRITICAL
            )
            # TODO: create BIG popup error
            raise PreventUpdate

        return naari_settings, False
