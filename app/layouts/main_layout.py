# app/layouts/main_layout.py

import dash_bootstrap_components as dbc
from dash import html, dcc
from app.layouts.header import header
from app.layouts.footer import footer
from app.components.modals import about_modal


def main_layout():
    return dbc.Container([
        # Header
        header(),
        
        # Main Content
        dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    id='patient-dropdown',
                    options=[],  # To be populated via callbacks
                    multi=True,
                    placeholder="Select Patients"
                )
            ], width=4),

            dbc.Col([
                dcc.DatePickerRange(
                    id='date-picker',
                    start_date_placeholder_text="Start Period",
                    end_date_placeholder_text="End Period",
                    display_format='YYYY-MM-DD'
                )
            ], width=4),

            dbc.Col([
                dbc.Button("About", id='about-button', color="info", className="mt-4")
            ], width=4)
        ], className="mb-4"),

        dbc.Row([
            dbc.Col([
                dcc.Graph(id='healing-progress-graph')
            ], width=6),

            dbc.Col([
                dcc.Graph(id='geographical-map')
            ], width=6)
        ], className="mb-4"),

        # About Modal
        about_modal(),

        # Footer
        footer()
    ], fluid=True)
