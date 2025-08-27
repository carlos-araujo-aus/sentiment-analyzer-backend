import requests
import uuid
from flask import Blueprint, jsonify, request, current_app
from .services.watson_service import analyze_text
from . import limiter, db
from .models import Analysis

main_bp = Blueprint('main', __name__)

# 2. Add the reCAPTCHA verification helper function
def verify_recaptcha(token):
    """Verifies a reCAPTCHA token with the Google API."""
    secret_key = current_app.config.get('RECAPTCHA_SECRET_KEY')

    # Fail securely if the secret key is not configured
    if not secret_key:
        current_app.logger.error('RECAPTCHA_SECRET_KEY is not configured.')
        return False

    payload = {'secret': secret_key, 'response': token}
    
    try:
        response = requests.post(
            'https://www.google.com/recaptcha/api/siteverify', 
            data=payload,
            timeout=5 
        )
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        result = response.json()
        return result.get('success', False)
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f'reCAPTCHA verification request failed: {e}')
        return False

@main_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    # 2. Get the same key that the rate limiter is using
    user_identifier = get_remote_address()
    
    # 3. Return this identifier in the response
    return jsonify({
        "status": "healthy",
        "limiter_key": user_identifier
    }), 200

@main_bp.route('/analyze', methods=['POST'])
def analyze_route():
    """
    Analyzes a block of text and saves the successful result to the database.
    First, it verifies the user with a reCAPTCHA token.
    """
    # --- 1. ADD SESSION ID VALIDATION ---
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        return jsonify({"error": "Session ID is missing from the request."}), 400

    if not request.is_json:
        return jsonify({"error": "Request must be of type application/json"}), 415

    data = request.get_json()

    # --- NEW: reCAPTCHA Verification Logic ---
    captcha_token = data.get('captchaToken')
    if not captcha_token or not verify_recaptcha(captcha_token):
        return jsonify({
            "error": "CAPTCHA verification failed. Please try again."
        }), 403 # 403 Forbidden is the appropriate status code

    # --- Existing logic continues only if CAPTCHA is valid ---
    text_to_analyze = data.get('text')

    if not text_to_analyze or not isinstance(text_to_analyze, str) or not text_to_analyze.strip():
        return jsonify({"error": "The 'text' field is required and must be a non-empty string."}), 400

    max_chars = current_app.config.get('MAX_TEXT_CHARS', 1000)
    if len(text_to_analyze) > max_chars:
        error_message = f"The text exceeds the character limit of {max_chars}. Submitted: {len(text_to_analyze)} characters."
        return jsonify({"error": error_message}), 413

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
            session_id=session_id, # <-- 2. INCLUDE SESSION ID ON SAVE
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
    Retrieves the 10 most recent analysis records for the current user's session.
    """
    # --- 3. ADD SESSION ID VALIDATION ---
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        return jsonify({"error": "Session ID is missing from the request."}), 400

    try:
        # --- 4. MODIFY THE DATABASE QUERY ---
        # Filter analyses to only return those for the current session
        recent_analyses = Analysis.query.filter_by(session_id=session_id).order_by(Analysis.created_at.desc()).limit(10).all()
        
        # Use the `to_dict()` method from our model to serialize each object.
        history_list = [analysis.to_dict() for analysis in recent_analyses]
        
        return jsonify(history_list), 200
    except Exception as e:
        # In a real production environment, this error should be logged.
        print(f"Database Error: Could not retrieve history. {e}")
        return jsonify({"error": "Could not retrieve analysis history."}), 500

# --- 2. ADD THE NEW ENDPOINT HERE ---
@main_bp.route('/session/new', methods=['GET'])
def new_session():
    """Generates and returns a new unique session ID (UUID)."""
    session_id = str(uuid.uuid4())
    return jsonify({"session_id": session_id}), 200