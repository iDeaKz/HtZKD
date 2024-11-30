# app/layouts/footer.py

import dash_bootstrap_components as dbc
from dash import html


def footer():
    return dbc.Container(
        dbc.Row(
            dbc.Col(
                html.Div(
                    [
                        html.Hr(),
                        html.P(
                            [
                                html.Span("© 2024 H(t) Zkaedi Healing Solution. All rights reserved.", className="mb-0")
                            ],
                            className="text-center",
                        ),
                    ]
                )
            )
        ),
        className="mt-4",
    )
