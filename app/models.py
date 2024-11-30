# app/models.py

from datetime import date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """
    User model for authentication and authorization.
    """

    __tablename__ = 'users'

    id: int = db.Column(db.Integer, primary_key=True)
    username: str = db.Column(db.String(150), unique=True, nullable=False)
    email: str = db.Column(db.String(150), unique=True, nullable=False)
    password_hash: str = db.Column(db.String(128), nullable=False)
    role: str = db.Column(db.String(50), nullable=False, default='Viewer')  # Roles: Admin, Healthcare Professional, Viewer

    def set_password(self, password: str) -> None:
        """
        Hashes and sets the user's password.

        Args:
            password (str): Plain-text password.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
        Verifies the user's password.

        Args:
            password (str): Plain-text password.

        Returns:
            bool: True if password is correct, False otherwise.
        """
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.username}>"


class Patient(db.Model):
    """
    Patient model to store healing progress data.
    """

    __tablename__ = 'patients'

    id: int = db.Column(db.Integer, primary_key=True)
    patient_id: int = db.Column(db.Integer, unique=True, nullable=False)
    date: date = db.Column(db.Date, nullable=False)
    healing_progress: float = db.Column(db.Float, nullable=False)

    def __repr__(self) -> str:
        return f"<Patient {self.patient_id}>"
