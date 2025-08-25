# api/config.py
import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'a-default-secret-key')
    # Character limit for the analysis
    MAX_TEXT_CHARS = 1000

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    FRONTEND_URL = os.getenv('FRONTEND_URL')