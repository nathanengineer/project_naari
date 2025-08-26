"""
Handles callbacks for the General tab in the Config Modal.

Currently manages editability of general setting inputs, with future expansion
planned for additional controls such as polling rates, global toggles, or
other system-wide configuration fields.
"""

from dash import Input, Output, MATCH

def general_settings_callback(app):
    """
       Register callbacks for the General Settings tab in the Config Modal.

       Includes:
            - Toggling the enabled/disabled state of general setting input fields

       This module is designed to support additional general configuration features in the future.
       """
    @app.callback(
        Output({'type': 'input_general_settings', "name": MATCH}, 'disabled'),
        Input({'type': 'edit_general_input_switch', "name": MATCH}, 'value')
    )

    def allow_for_setting_edit(value):
        """ Callback function allows for Specific Widget to be editable. """
        if value:
            return False
        return True
