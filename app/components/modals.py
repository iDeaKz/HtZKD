# app/components/modals.py

import dash_bootstrap_components as dbc
from dash import html


def about_modal():
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("About")),
            dbc.ModalBody("H(t) Zkaedi Healing Solution Dashboard provides comprehensive insights into patient healing processes."),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-about", className="ms-auto", n_clicks=0)
            ),
        ],
        id="about-modal",
        is_open=False,
    )
