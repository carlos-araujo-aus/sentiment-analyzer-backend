# api/services/watson_service.py
import os
import json
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_cloud_sdk_core.api_exception import ApiException
from ibm_watson.natural_language_understanding_v1 import Features, SentimentOptions, EmotionOptions, KeywordsOptions

def analyze_text(text_to_analyze):
    """
    Analyzes the text using the IBM Watson API and returns a structured dictionary.
    """
    api_key = os.getenv('WATSON_API_KEY')
    api_url = os.getenv('WATSON_URL')

    if not api_key or not api_url:
        return {"error": "Watson API credentials are not configured.", "status": 500}

    try:
        authenticator = IAMAuthenticator(api_key)
        nlu_service = NaturalLanguageUnderstandingV1(
            version='2022-04-07',
            authenticator=authenticator
        )
        nlu_service.set_service_url(api_url)

        analysis = nlu_service.analyze(
            text=text_to_analyze,
            features=Features(
                sentiment=SentimentOptions(),
                emotion=EmotionOptions(),
                keywords=KeywordsOptions(limit=5)
            )
        ).get_result()

        # --- DEBUGGING PRINT ---
        print("--- RAW RESPONSE FROM IBM WATSON ---")
        print(json.dumps(analysis, indent=2))
        print("------------------------------------")

        # --- CORRECT LOGIC: Structure the REAL result ---
        result = {
            "sentiment": analysis.get("sentiment", {}).get("document", {}),
            # --- THIS IS THE FIX ---
            # Use "emotion" (singular) to match the actual API response key
            "emotions": analysis.get("emotion", {}).get("document", {}).get("emotion", {}),
            "keywords": analysis.get("keywords", [])
        }
        
        return {"data": result, "status": 200}
    
    except ApiException as e:
        return {"error": f"Watson API Error: {str(e)}", "status": e.code}
    
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}", "status": 500}
