"""
Main Dash app bootstrap for the WLED Controller.

- Builds the top-level layout (navbar, sidebar, main content, hidden stores).
- Loads initial config + a first pass of device status/presets for a snappier first paint.
- Registers callback groups (status, content, config, modes, page-load).

"""
from __future__ import annotations

import logging
import os
import sys
from traceback import format_exc
# This is here bellow to handle directory pathway shenanigans
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from dash import Dash, html, dcc, Output, Input, State
import dash_bootstrap_components as dbc


#------------------------- NAARI Dependencies ---------------------------------------------#
from naari_logging.naari_logger import LogManager
logger = LogManager()
logger.setup_file_logging()

from naari_app.util.util_functions import naari_config_load

from naari_app.ui_parts.navbar import navbar
from naari_app.ui_parts.sidebar import sidebar
from naari_app.ui_parts.popups import refresh_popup

from naari_app.modals.config_modal import config_modal

from naari_app.callbacks.startup_callbacks import startup_callbacks
from naari_app.callbacks.ui_refresh_callbacks import layout_refresh_callbacks
from naari_app.callbacks.status_callbacks import status_callbacks
from naari_app.callbacks.device_controls_callbacks import device_controls_callbacks
from naari_app.callbacks.global_controls_callbacks import global_controls_callback
from naari_app.callbacks.content_callback import main_content_callback
from naari_app.callbacks.config_callbacks import config_callbacks
from naari_app.callbacks.theme_settings_callback import theme_settings_callback
from naari_app.callbacks.device_settings_callback import device_settings_callback
from naari_app.callbacks.general_settings_callback import general_settings_callback



MAINDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Pointing to the specific targeted .env file due to directory shenanigans
load_dotenv(os.path.join(MAINDIR, ".env"))

HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))
DEBUG = os.getenv("DEBUG") == "1"
RELOADER = os.getenv("USE_RELOADER") == "1"  # keep off while debugging async
TO_LOG = int(os.getenv("LOGGING", "0")) == 1

def app_layout():
    """
    Build the main layout for initial page load.

    Loads configuration, performs a single initial poll for:
      - device status (/json)
      - device presets (/presets.json)

    Returns:
        A Dash Bootstrap Container containing the entire app layout.
    """

    naari_settings = naari_config_load()

    return dbc.Container(
        id = "app-container",
        fluid=True,
        children=[
            html.Div(
                children=[
                    dcc.Location(id='url', refresh=False),
                    # converting interval from sec -> ms
                    dcc.Interval(id='poll_interval', interval=(naari_settings['ui_settings']['polling_rate']['value'] * 1000), n_intervals=0, disabled=True),
                    dcc.Store("reset_poll_interval", data=False, storage_type='session'),

                    # Hidden stores (default shapes matter for downstream callbacks)
                    dcc.Store(id='naari_settings', data=naari_settings, storage_type='session'),
                    dcc.Store(id ='initial_device_catch_data', data=None, storage_type='session'),
                    dcc.Store(id='device_catch_data', data=None, storage_type='session'),
                    dcc.Store(id='devices_catch_presets', data=None, storage_type='session'),

                    # For Initial Calls, Chains, and preventions
                    dcc.Store(id='elements_initialized', data=None, storage_type='session'),
                    dcc.Store(id='data_app_load_check', data=False, storage_type='session'),
                    dcc.Store(id='init_brightness_chain_trigger', data=None, storage_type='session'),
                    html.Div(id='brightness_chain_trigger', n_clicks=0),

                    dcc.Store(id='auto_mode', data=False),  # Initial_Auto_Mode

                    refresh_popup()
                ]
            ),
            html.Div(
                id='config_modal_container',
                children=config_modal(naari_settings)
            ),
            html.Div(navbar()),
            dbc.Row(children=[
                dbc.Col(
                    id='app_sidebar',
                    xs=12,
                    md=3,
                    children=sidebar(naari_settings.get('themes'))
                ),
                dbc.Col(
                    id='app_main_content',
                    xs=12,
                    md=9,
                    children=[] # Uses callback to provide smoother rendering due to any config changes
                )
            ]),
            html.Div(id='master-dumb-dash-1', style={'display': "none"})
        ]
    )

def dash_app():
    """ Create and Configures the Dash App"""
    app = Dash(
        name="WLEDController",
        update_title='WLED Controller',
        prevent_initial_callbacks="initial_duplicate",
        external_stylesheets=[
            dbc.themes.DARKLY,
            "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css"
        ]
    )

    # Custom HTML shell (keeps <title> fixed)
    app.index_string = """
        <!DOCTYPE html>
        <html>
            <head>
                {%metas%}
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>WLED Controller</title>  <!-- This stays fixed -->
                {%favicon%}
                {%css%}
            </head>
            <body>
                {%app_entry%}
                <footer>
                    {%config%}
                    {%scripts%}
                    {%renderer%}
                </footer>
            </body>
        </html>
    """

    # callable so layout is re-evaluated on hard refresh
    app.layout =  app_layout()

    # register your callback groups (they already take `app`)
    startup_callbacks(app)
    layout_refresh_callbacks(app)
    status_callbacks(app)
    device_controls_callbacks(app)
    main_content_callback(app)
    global_controls_callback(app)
    config_callbacks(app)
    theme_settings_callback(app)
    device_settings_callback(app)
    general_settings_callback(app)


    # Segment bellow is currently the only way to prevent and setup a global prevent 'Initial Call' due to using dynamic widgets and callbacks
    @app.callback(
        Output('elements_initialized', 'data'),
        Input('device_catch_data', 'data'),
        State('elements_initialized', 'data')
    )
    def elements_started(_, prev):
        """Mark the app as initialized once device data has been set at least once."""
        return True

    return app


if __name__ == '__main__':
    try:
        the_app = dash_app()
        the_app.run(debug=DEBUG, host=HOST, port=PORT, threaded=True, use_reloader=RELOADER)
    except Exception as err:        # pylint: disable=broad-exception-caught

        logger.print_message(
            "Major problem during run >> %s \ntraceback >> %s",
            err, format_exc(),
            to_log=TO_LOG,
            log_level=logging.CRITICAL
        )
    finally:
        logger.shutdown()
