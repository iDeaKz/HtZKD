# app/__init__.py

import logging
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import dash
import dash_bootstrap_components as dbc

from app.config import Config
from app.models import db
from app.layouts.main_layout import main_layout
from app.callbacks.update_graphs import register_callbacks
from app.callbacks.user_interactions import register_user_callbacks

# Load environment variables from .env
load_dotenv()

def create_app() -> Flask:
    """
    Creates and configures the Flask application.

    Returns:
        Flask: Configured Flask application.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    # Setup logging
    setup_app_logging(app)

    # User loader callback
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id: int) -> User:
        return User.query.get(int(user_id))

    # Initialize Dash
    dash_app = dash.Dash(
        __name__,
        server=app,
        routes_pathname_prefix='/',
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        assets_folder='app/assets'
    )

    # Set the layout
    dash_app.layout = main_layout

    # Register callbacks
    register_callbacks(dash_app)
    register_user_callbacks(dash_app)

    return app


def setup_app_logging(app: Flask) -> None:
    """
    Sets up logging for the Flask application.

    Args:
        app (Flask): Flask application instance.
    """
    if not os.path.exists('logs'):
        os.makedirs('logs')

    handler = logging.handlers.RotatingFileHandler(
        'logs/app.log', maxBytes=100000, backupCount=10
    )
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Application startup')


if __name__ == "__main__":
    app = create_app()
    app.run(
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', 8050)),
        debug=bool(os.getenv('DEBUG', False))
    )
