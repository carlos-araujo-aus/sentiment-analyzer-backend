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

def get_identifier():
    """
    Determina el identificador para el límite de peticiones.
    Excluye las peticiones OPTIONS del límite de peticiones.
    """
    if request.method == 'OPTIONS':
        return None
    # Para la protección de ráfagas, la IP es un buen identificador.
    return get_remote_address()

# --- Initialize Extensions ---
db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(
    key_func=get_identifier
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

    # --- Extension Initialization ---
    db.init_app(app)
    migrate.init_app(app, db)
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
