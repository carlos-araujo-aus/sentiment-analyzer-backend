# api/routes.py
from flask import Blueprint, jsonify, request, current_app
from .services.watson_service import analyze_text
from . import limiter

# Create a Blueprint for our main routes
main_bp = Blueprint('main', __name__)

@main_bp.route('/health')
def health_check():
    """
    Health check endpoint for monitoring.
    """
    return jsonify({"status": "healthy"}), 200

@main_bp.route('/analyze', methods=['POST'])
@limiter.limit("10 per minute") # Specific rate limit for this route
def analyze_route():
    """
    Analyzes a block of text for sentiment, emotions, and keywords.
    """
    # 1. Validate that the request is in JSON format
    if not request.is_json:
        return jsonify({"error": "Request must be of type application/json"}), 415

    data = request.get_json()
    text_to_analyze = data.get('text')

    # 2. Validate the presence and type of the input
    if not text_to_analyze or not isinstance(text_to_analyze, str) or not text_to_analyze.strip():
        return jsonify({"error": "The 'text' field is required and must be a non-empty string."}), 400

    # 3. Validate the length of the input against our config
    max_chars = current_app.config['MAX_TEXT_CHARS']
    if len(text_to_analyze) > max_chars:
        return jsonify({"error": f"The text exceeds the character limit of {max_chars}."}), 413

    # Call the service layer to perform the analysis
    result = analyze_text(text_to_analyze)
    status_code = result.get("status", 500)

    # Return the result from the service layer
    if "error" in result:
        return jsonify({"error": result["error"]}), status_code

    return jsonify(result.get("data")), 200