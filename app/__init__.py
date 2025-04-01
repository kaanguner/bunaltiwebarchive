# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config.settings import Config # Import from your config file path
import os

# Globally accessible libraries
db = SQLAlchemy()

def create_app(config_class=Config):
    """Initialize the core application."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_class)

    print(f"--- Initializing App ---")
    print(f"Database URI Loaded: {app.config['SQLALCHEMY_DATABASE_URI'][:30]}...") # Verify URI loaded

    # Initialize Plugins
    db.init_app(app)

    # The 'with app.app_context()' is often used for operations needing app context
    # during initialization, like db.create_all(). Blueprint registration
    # can technically happen outside it, but keeping it here is fine.
    with app.app_context():
        # ============================================
        # == START Replace this section ==
        # ============================================

        # --- CORRECTED IMPORT ---
        # Import the 'bp' object directly from the app/main.py module
        # (assuming main.py is directly inside 'app' folder now)
        # and give it an alias 'main_bp' to avoid name conflicts if needed.
        try:
            # Use a try-except block during debugging if imports are tricky
            from .models.main import bp as main_bp # Point to .models.main
            print("--- Successfully imported 'bp' from app/main.py ---")
        except ImportError as e:
            print(f"--- ERROR importing blueprint: {e} ---")
            # Handle the error appropriately, maybe raise it again
            # For now, we'll let it raise implicitly if import fails

        # --- CORRECTED REGISTRATION ---
        # Register the imported blueprint object directly
        try:
            app.register_blueprint(main_bp)
            print(f"--- Registered blueprint: {main_bp.name} ---")
        except NameError:
             print(f"--- ERROR: 'main_bp' was not defined, likely due to import error above. ---")
        except Exception as e:
             print(f"--- ERROR registering blueprint: {e} ---")


        # ============================================
        # == END Replace this section ==
        # ============================================


        # Optional: Create tables if they don't exist (better handled by migrations later)
        # print("Creating database tables if they don't exist...")
        # db.create_all()
        # print("Tables checked/created.")

        print("--- App Initialization Complete ---")
        return app

# If you have models defined, make sure they are imported somewhere
# after 'db' is initialized but before they are needed. Often done
# within the blueprint's routes or models package init.
# Example: from . import models # If you have an app/models/__init__.py