import dash_bootstrap_components as dbc
from dash import html, dcc

# Note: function was/is an attempt to use Modal as a quick popup window. Not functional yet.
def something_else_popup(model_id='refresh_popup'):
    return html.Div(
        id=f'{model_id}_trigger',
        n_clicks=0,
        children=[
            dcc.Interval(id=f'{model_id}_auto_close', interval=2000, n_intervals=0, disabled=True),
            dbc.Modal(
                id=model_id,
                centered=True,
                is_open=False,
                fade=True,
                children=[
                    dbc.ModalHeader(dbc.ModalTitle("Refresh Status"), close_button=False),
                    dbc.ModalBody(id=f'{model_id}_body')
                ]
            )
        ]
    )


def refresh_popup() -> dbc.Alert:
    """ Display refresh status upon activation. Popup reacts according to the Callback. """
    return dbc.Alert(
        id='refresh_popup',
        is_open=False,
        color='light',
        duration=2000,
        fade=True,
        children=[]
    )
