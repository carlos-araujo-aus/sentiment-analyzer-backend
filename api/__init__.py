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
# Asegúrate de que el constructor de Limiter NO tenga 'exempt_methods'
limiter = Limiter(
    key_func=get_remote_address,
    # This is the single source of truth for our rate limit.
    default_limits=["10 per day"]
)

def create_app(config_class_string='api.config.ProductionConfig'):
    """
    Application factory pattern to create and configure the Flask app.
    """
    app = Flask(__name__)
    app.config.from_object(config_class_string)

    # --- Database Config ---
    db_url = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url + "?sslmode=require"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- Rate Limiter Config ---
    # SET THE CONFIGURATION BEFORE INITIALIZING THE EXTENSION.
    # This ensures the limiter reads this config when it's initialized.
    app.config["RATELIMIT_EXEMPT_METHODS"] = ["OPTIONS"]

    # --- Extension Initialization ---
    db.init_app(app)
    migrate.init_app(app, db)
    # Now, when the limiter is initialized, it will see the config above.
    limiter.init_app(app)
    
    # --- CORS ---
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

    return app
