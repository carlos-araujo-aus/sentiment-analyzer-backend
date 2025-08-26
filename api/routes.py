# api/routes.py
from flask import Blueprint, jsonify, request, current_app
from .services.watson_service import analyze_text
from . import limiter, db
from .models import Analysis

main_bp = Blueprint('main', __name__)

@main_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({"status": "healthy"}), 200

@main_bp.route('/analyze', methods=['POST'])
@limiter.limit("10 per minute")
def analyze_route():
    """
    Analyzes a block of text and saves the successful result to the database.
    """
    if not request.is_json:
        return jsonify({"error": "Request must be of type application/json"}), 415

    data = request.get_json()
    text_to_analyze = data.get('text')

    if not text_to_analyze or not isinstance(text_to_analyze, str) or not text_to_analyze.strip():
        return jsonify({"error": "The 'text' field is required and must be a non-empty string."}), 400

    max_chars = current_app.config.get('MAX_TEXT_CHARS', 1000)
    if len(text_to_analyze) > max_chars:
        return jsonify({"error": f"The text exceeds the character limit of {max_chars}."}), 413

    # Call the service layer to perform the analysis
    result = analyze_text(text_to_analyze)
    status_code = result.get("status", 500)

    if "error" in result:
        return jsonify({"error": result["error"]}), status_code

    # --- New Database Logic ---
    # If the analysis was successful, save the results to the database.
    try:
        analysis_data = result.get("data", {})
        sentiment_data = analysis_data.get("sentiment", {})
        emotions_data = analysis_data.get("emotions", {})
        
        new_analysis = Analysis(
            text_content=text_to_analyze,
            sentiment_label=sentiment_data.get('label', 'unknown'),
            sentiment_score=sentiment_data.get('score', 0.0),
            emotion_joy=emotions_data.get('joy', 0.0),
            emotion_sadness=emotions_data.get('sadness', 0.0),
            emotion_fear=emotions_data.get('fear', 0.0),
            emotion_disgust=emotions_data.get('disgust', 0.0),
            emotion_anger=emotions_data.get('anger', 0.0),
            keywords=analysis_data.get('keywords', [])
        )
        
        db.session.add(new_analysis)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # In a real production environment, this error should be logged.
        print(f"Database Error: Could not save analysis. {e}")
        # We don't return an error to the user because the analysis itself
        # was successful. The user gets their result, even if we failed to save it.

    # The user receives the analysis data, regardless of the DB operation outcome.
    return jsonify(result.get("data")), 200

# --- New Endpoint ---
@main_bp.route('/history', methods=['GET'])
def history_route():
    """
    Retrieves the 10 most recent analysis records from the database.
    """
    try:
        # Query the database for the last 10 analyses, ordered by creation date descending.
        recent_analyses = Analysis.query.order_by(Analysis.created_at.desc()).limit(10).all()
        
        # Use the `to_dict()` method from our model to serialize each object.
        history_list = [analysis.to_dict() for analysis in recent_analyses]
        
        return jsonify(history_list), 200
    except Exception as e:
        # In a real production environment, this error should be logged.
        print(f"Database Error: Could not retrieve history. {e}")
        return jsonify({"error": "Could not retrieve analysis history."}), 500