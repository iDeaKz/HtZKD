# tests/__init__.py

import pytest
from app import create_app
from app.models import db as _db
import os
import tempfile


@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test session."""
    db_fd, db_path = tempfile.mkstemp()
    os.environ['DATABASE_URL'] = f"sqlite:///{db_path}"

    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

    with app.app_context():
        _db.create_all()
        yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope='session')
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(scope='function')
def db(app):
    """Create a new database for the test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()
