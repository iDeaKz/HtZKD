# app/callbacks/user_interactions.py

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from flask_login import current_user, login_user, logout_user
from flask import redirect, url_for
import dash_bootstrap_components as dbc
from dash import html

from app.models import User


def register_user_callbacks(dash_app):
    """
    Registers user interaction callbacks with the Dash application.

    Args:
        dash_app (dash.Dash): Dash application instance.
    """

    @dash_app.callback(
        Output("about-modal", "is_open"),
        [Input("about-button", "n_clicks"), Input("close-about", "n_clicks")],
        [State("about-modal", "is_open")],
    )
    def toggle_about_modal(n1: int, n2: int, is_open: bool) -> bool:
        """
        Toggles the visibility of the About modal.

        Args:
            n1 (int): Number of clicks on the About button.
            n2 (int): Number of clicks on the Close button.
            is_open (bool): Current state of the modal.

        Returns:
            bool: New state of the modal.
        """
        ctx = callback_context

        if not ctx.triggered:
            raise PreventUpdate
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if button_id == "about-button" and n1:
            return True
        elif button_id == "close-about" and n2:
            return False
        return is_open


    @dash_app.callback(
        Output("login-output", "children"),
        [Input("login-button", "n_clicks")],
        [
            State("username-input", "value"),
            State("password-input", "value"),
        ],
    )
    def login(n_clicks: int, username: str, password: str) -> str:
        """
        Handles user login.

        Args:
            n_clicks (int): Number of clicks on the login button.
            username (str): Username input.
            password (str): Password input.

        Returns:
            str: Login status message.
        """
        if not n_clicks:
            raise PreventUpdate

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return "Login successful!"
        else:
            return "Invalid username or password."


    @dash_app.callback(
        Output("logout-output", "children"),
        [Input("logout-button", "n_clicks")],
    )
    def logout(n_clicks: int) -> str:
        """
        Handles user logout.

        Args:
            n_clicks (int): Number of clicks on the logout button.

        Returns:
            str: Logout status message.
        """
        if not n_clicks:
            raise PreventUpdate

        logout_user()
        return "You have been logged out."


    @dash_app.server.route("/login")
    def login_route():
        """
        Redirects to the login page.

        Returns:
            flask.Response: Redirect response.
        """
        return redirect(url_for("login"))


    @dash_app.server.route("/logout")
    def logout_route():
        """
        Redirects to the logout page.

        Returns:
            flask.Response: Redirect response.
        """
        return redirect(url_for("logout"))
