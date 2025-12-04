"""
API Routes Module
-----------------
Defines all HTTP endpoints for the application.
Separates page routes from API routes using blueprints.
"""

import logging
from flask import Blueprint, render_template, request, jsonify

from web.handlers import ChatHandler

logger = logging.getLogger(__name__)

# Blueprint for page routes
pages_blueprint = Blueprint("pages", __name__)

# Blueprint for API endpoints
api_blueprint = Blueprint("api", __name__)

# Lazy-initialized handler
_chat_handler = None


def _get_chat_handler() -> ChatHandler:
    """Lazy initialization of chat handler."""
    global _chat_handler
    if _chat_handler is None:
        _chat_handler = ChatHandler()
    return _chat_handler


# ============================================================================
# Page Routes
# ============================================================================

@pages_blueprint.route("/")
def home_page():
    """Render the main conversation interface."""
    return render_template("conversation.html")


@pages_blueprint.route("/health")
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "HealthAI Assistant"
    })


# ============================================================================
# API Routes
# ============================================================================

@api_blueprint.route("/chat", methods=["POST"])
def process_chat_message():
    """
    Process incoming chat messages and return AI responses.
    
    Expected payload:
        - message: User's message text
    
    Returns:
        JSON response with generated answer
    """
    handler = _get_chat_handler()
    
    # Handle form data (from HTML form)
    user_message = request.form.get("message") or request.form.get("msg")
    
    # Handle JSON payload
    if not user_message and request.is_json:
        data = request.get_json()
        user_message = data.get("message")
    
    if not user_message:
        logger.warning("Empty message received")
        return jsonify({
            "error": "No message provided",
            "success": False
        }), 400
    
    logger.debug(f"Processing message: {user_message[:50]}...")
    
    response = handler.handle_user_message(user_message)
    
    # Return plain text for form submissions (backward compat)
    if request.form:
        return response["answer"]
    
    return jsonify(response)


@api_blueprint.route("/chat/detailed", methods=["POST"])
def process_detailed_query():
    """
    Process queries and return detailed responses with sources.
    
    Returns response with context information for transparency.
    """
    handler = _get_chat_handler()
    
    if not request.is_json:
        return jsonify({"error": "JSON payload required"}), 400
    
    data = request.get_json()
    user_message = data.get("message")
    
    if not user_message:
        return jsonify({"error": "Message field required"}), 400
    
    response = handler.handle_detailed_query(user_message)
    return jsonify(response)


@api_blueprint.route("/status", methods=["GET"])
def api_status():
    """Return API status and version information."""
    return jsonify({
        "api_version": "1.0.0",
        "status": "operational",
        "endpoints": ["/api/chat", "/api/chat/detailed", "/api/status"]
    })
