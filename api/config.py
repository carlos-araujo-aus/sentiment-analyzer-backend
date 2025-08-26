# api/config.py
import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'a-default-secret-key')
    # Character limit for the analysis
    MAX_TEXT_CHARS = 1000

    # Flask-Limiter configurations
    # Enable the rate limiter
    RATELIMIT_ENABLED = True
    # Store rate limit data in memory. For production, you might use "redis://..."
    RATELIMIT_STORAGE_URI = "memory://"
    # Send rate limit headers in the response
    RATELIMIT_HEADERS_ENABLED = True

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    FRONTEND_URL = os.getenv('FRONTEND_URL')