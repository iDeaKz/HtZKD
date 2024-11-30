# app/callbacks/__init__.py

from .update_graphs import register_callbacks
from .user_interactions import register_user_callbacks

__all__ = ['register_callbacks', 'register_user_callbacks']
