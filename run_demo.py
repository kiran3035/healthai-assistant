"""
HealthAI Assistant - Demo Mode Entry Point
------------------------------------------
Run this script to start the demo server (no AWS/AI services required).
This demonstrates the UI and basic functionality.
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify
import random

from flask import Flask, render_template, request, jsonify, Blueprint
import random

# Demo responses for testing without AI services
DEMO_RESPONSES = [
    "Based on medical literature, that's an important health topic. For personalized advice, please consult a healthcare provider.",
    "This is a common health concern. The general guidance suggests maintaining a balanced lifestyle, but individual cases may vary.",
    "From the knowledge base: This condition often relates to lifestyle factors. Regular check-ups are recommended.",
    "That's a great question about health. While I can provide general information, specific medical advice should come from a doctor.",
    "According to medical references, this is something many people ask about. Prevention often includes healthy habits.",
]

def create_demo_app():
    app = Flask(
        __name__,
        template_folder="assets/views",
        static_folder="assets/styles",
        static_url_path="/styles"
    )

    app.config["SECRET_KEY"] = "demo-mode-key"

    # Create blueprints to match main app structure
    pages_blueprint = Blueprint("pages", __name__, static_folder="../assets/styles", static_url_path="/styles")
    api_blueprint = Blueprint("api", __name__)

    @pages_blueprint.route("/")
    def home_page():
        """Render the main conversation interface."""
        return render_template("conversation.html")

    @pages_blueprint.route("/health")
    def health_check():
        """Simple health check endpoint."""
        return jsonify({
            "status": "healthy",
            "service": "HealthAI Assistant (Demo Mode)",
            "mode": "demo"
        })

    @api_blueprint.route("/chat", methods=["POST"])
    def process_chat_message():
        """Process chat messages with demo responses."""
        user_message = request.form.get("message") or request.form.get("msg")
        
        if not user_message and request.is_json:
            data = request.get_json()
            user_message = data.get("message")
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        # Generate demo response
        response = random.choice(DEMO_RESPONSES)
        response = f"[DEMO MODE] {response}"
        
        # Return plain text for form submissions
        if request.form:
            return response
        
        return jsonify({
            "success": True,
            "answer": response,
            "message_received": user_message,
            "mode": "demo"
        })

    @api_blueprint.route("/status", methods=["GET"])
    def api_status():
        """Return API status."""
        return jsonify({
            "api_version": "1.0.0",
            "status": "operational",
            "mode": "demo",
            "note": "Running in demo mode - no AI services connected"
        })

    # Register blueprints
    app.register_blueprint(pages_blueprint)
    app.register_blueprint(api_blueprint, url_prefix="/api")

    return app

app = create_demo_app()


def main():
    """Application entry point."""
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║         HealthAI Assistant v1.0.0 (DEMO)             ║
    ╠══════════════════════════════════════════════════════╣
    ║  🎭 Running in DEMO MODE                             ║
    ║  No AWS services required for this demo              ║
    ╠══════════════════════════════════════════════════════╣
    ║  Starting development server...                      ║
    ║  Access the application at:                          ║
    ║  http://localhost:5000                               ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    app.run(host="0.0.0.0", port=5001, debug=True)


if __name__ == "__main__":
    main()
