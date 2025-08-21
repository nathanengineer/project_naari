""" Modular that contains backend callbacks for the "General Settings Tab in the Config Modal. """

from dash import Input, Output, MATCH

def general_settings_callback(app):

    @app.callback(
        Output({'type': 'input_general_settings', "name": MATCH}, 'disabled'),
        Input({'type': 'edit_general_input_switch', "name": MATCH}, 'value')
    )

    def allow_for_setting_edit(value):
        """ Callback function allows for Specific Widget to be editable. """
        if value:
            return False
        return True
