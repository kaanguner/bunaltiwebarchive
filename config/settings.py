# config/settings.py
import os
from dotenv import load_dotenv

# Define the base directory of the project
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # Points to the root folder
# Load the .env file from the base directory
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Set Flask configuration vars from .env file."""

    # General Config
    SECRET_KEY = os.environ.get('SECRET_KEY')
    FLASK_APP = os.environ.get('FLASK_APP')
    FLASK_ENV = os.environ.get('FLASK_ENV')

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False # Silence the deprecation warning