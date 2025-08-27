from dash import Input, Output, MATCH

def main_content_callback(app):

    @app.callback(
        Output({'type': 'collapse_segment', 'device_id': MATCH}, 'is_open'),
        Input({'type': 'active_device_collapse_button', 'device_id': MATCH}, 'n_clicks'),
    )
    def collapse_element(clicks):
        # Even = True (collapse element = open)
        # Odd = False (collapse element = close)
        return not bool(clicks % 2)
