# api/__init__.py
import os
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_swagger_ui import get_swaggerui_blueprint
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize extensions
# We create the instances here but bind them to the app inside the factory
limiter = Limiter(key_func=get_remote_address, default_limits=["10 per day", "10 per hour"])
# (Database instances will be added in a later phase)

def create_app(config_class='api.config.ProductionConfig'):
    """
    Application Factory: Creates and configures the Flask application.
    """
    app = Flask(__name__)
    # Load configuration from the config.py file
    app.config.from_object(config_class)

    # --- CONFIGURE EXTENSIONS ---
    # CORS: Allow requests from our frontend
    frontend_url = app.config.get('FRONTEND_URL')
    if frontend_url:
        # Production: strict CORS
        CORS(app, origins=[frontend_url])
    else:
        # Development: permissive CORS
        CORS(app)

    # Rate Limiter
    limiter.init_app(app)

    # Swagger UI for API documentation
    SWAGGER_URL = '/api/docs'  # URL for the interactive API docs
    API_URL = '/static/swagger.json' # URL to the API specification file (we will create this later)
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL, API_URL, config={'app_name': "Sentiment Analyzer API"}
    )
    app.register_blueprint(swaggerui_blueprint)

    # --- REGISTER BLUEPRINTS ---
    from .routes import main_bp
    # All routes in this blueprint will be prefixed with /api
    app.register_blueprint(main_bp, url_prefix='/api')

    return app
