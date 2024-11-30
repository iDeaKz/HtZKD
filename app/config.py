# app/config.py

import os


class Config:
    # General Config
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Other Configurations
    API_KEY = os.getenv('API_KEY', '')
    DATA_PATH = os.getenv('DATA_PATH', 'app/data/')
    GEOJSON_PATH = os.getenv('GEOJSON_PATH', 'app/data/geojson/')
