# app/layouts/header.py

import dash_bootstrap_components as dbc
from dash import html


def header():
    return dbc.Navbar(
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(html.Img(src="/assets/logo.png", height="40px")),
                        dbc.Col(dbc.NavbarBrand("H(t) Zkaedi Healing Solution", className="ms-2")),
                    ],
                    align="center",
                    className="g-0",
                ),
                dbc.NavbarToggler(id="navbar-toggler"),
                dbc.Collapse(
                    dbc.Nav(
                        [
                            dbc.NavItem(dbc.NavLink("Home", href="#")),
                            dbc.NavItem(dbc.NavLink("Reports", href="#")),
                            dbc.NavItem(dbc.NavLink("Settings", href="#")),
                            dbc.NavItem(dbc.NavLink("Logout", href="#")),
                        ],
                        className="ms-auto",
                        navbar=True,
                    ),
                    id="navbar-collapse",
                    navbar=True,
                ),
            ]
        ),
        color="dark",
        dark=True,
        className="mb-4",
    )
