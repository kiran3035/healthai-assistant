"""
Flask Web Server Module
-----------------------
Application factory for creating and configuring the Flask application.
Implements blueprint-based architecture for modular routing.
"""

import logging
from flask import Flask

from config.settings import get_settings

logger = logging.getLogger(__name__)


def create_application() -> Flask:
    """
    Application factory to create and configure the Flask app.
    
    Returns:
        Configured Flask application instance.
    """
    settings = get_settings()
    
    app = Flask(
        __name__,
        template_folder="../assets/views",
        static_folder="../assets/styles",
        static_url_path="/styles"
    )
    
    # Configure application
    app.config["SECRET_KEY"] = "healthai-secure-key-change-in-production"
    app.config["APP_NAME"] = settings.app_name
    
    # Register blueprints
    _register_blueprints(app)
    
    # Configure logging
    _setup_logging(app, settings.server.debug)
    
    logger.info(f"Application '{settings.app_name}' initialized")
    
    return app


def _register_blueprints(app: Flask) -> None:
    """Register all application blueprints."""
    from web.routes import api_blueprint, pages_blueprint
    
    app.register_blueprint(pages_blueprint)
    app.register_blueprint(api_blueprint, url_prefix="/api")
    
    logger.debug("Blueprints registered successfully")


def _setup_logging(app: Flask, debug: bool) -> None:
    """Configure application logging."""
    log_level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Suppress verbose library logs
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("pinecone").setLevel(logging.WARNING)


def run_development_server() -> None:
    """Start the development server with hot reloading."""
    settings = get_settings()
    app = create_application()
    
    logger.info(
        f"Starting development server at http://{settings.server.host}:{settings.server.port}"
    )
    
    app.run(
        host=settings.server.host,
        port=settings.server.port,
        debug=settings.server.debug
    )
