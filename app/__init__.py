"""
Hacky News Application - Factory Pattern Implementation
"""
import logging
import os
from flask import Flask, send_from_directory
from flask_cors import CORS

from app.models.database import setup_db, ensure_test_data
from app.config.settings import DEBUG, PORT, HOST
from app.api.routes import api_bp

def create_app(test_config=None):
    """
    Application factory function that creates and configures the Flask app.
    
    Args:
        test_config: Configuration to use for testing.
        
    Returns:
        Flask application instance
    """
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if DEBUG else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting Hacky News application")
    
    # Create and configure the app
    app = Flask(__name__, 
                static_folder='../static',
                static_url_path='/static',
                template_folder='../templates')
    
    # Apply test configuration if provided
    if test_config:
        app.config.from_mapping(test_config)
    
    # Enable CORS
    CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Add CORS headers to all responses
    @app.after_request
    def after_request(response):
        """Add CORS headers to all responses"""
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    # Ensure database is set up and has test data
    setup_db()
    ensure_test_data()
    
    return app