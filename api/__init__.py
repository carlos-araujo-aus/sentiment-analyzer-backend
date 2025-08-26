# api/__init__.py
import os
from flask import Flask, request, current_app
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_swagger_ui import get_swaggerui_blueprint
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

load_dotenv()

# --- Initialize Extensions ---
# Create instances of our extensions globally.
# They are not yet attached to a specific app.
db = SQLAlchemy()
migrate = Migrate()
# Initialize the rate limiter. It will be configured from the app config.
limiter = Limiter(
    key_func=lambda: get_remote_address() or request.remote_addr,
    default_limits=["50 per day", "10 per hour"]
    # We removed storage_uri from here
)

def create_app(config_class='api.config.ProductionConfig'):
    """
    Application factory pattern to create and configure the Flask app.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # --- Configure and Bind Extensions to the App ---

    # Database Configuration
    # Read the database URI from environment variables
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL') + "?sslmode=require"
    # Disable a feature of SQLAlchemy that we don't need and that adds overhead
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Bind the database and migration engine to the Flask app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # CORS Configuration
    frontend_url = app.config.get('FRONTEND_URL')
    if frontend_url:
        CORS(app, origins=[frontend_url])
    else:
        CORS(app)  # Permissive for development

    # Swagger UI Configuration
    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.json'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL, API_URL, config={'app_name': "Sentiment Analyzer API"}
    )
    app.register_blueprint(swaggerui_blueprint)

    # --- Register Blueprints ---
    from .routes import main_bp
    app.register_blueprint(main_bp, url_prefix='/api')

    # Bind the rate limiter AFTER the blueprints are registered.
    limiter.init_app(app)

    return app
