import re
import joblib
import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Config
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "custom_lang_id.joblib")

# Hinglish Heuristics (Common Hindi words in Latin script)
HINGLISH_DICTIONARY = ["kya", "hai", "tum", "nahi", "mil raha", "scheme", "free", "baat", "kaise"]

class LanguageDetector:
    def __init__(self):
        self.model = None
        self.load_model()

    def load_model(self):
        """Load the trained Scikit-Learn model"""
        try:
            if os.path.exists(MODEL_PATH):
                self.model = joblib.load(MODEL_PATH)
                logger.info(f"Language model loaded from {MODEL_PATH}")
            else:
                logger.warning(f"Language model NOT found at {MODEL_PATH}. Feature 1 will be limited.")
        except Exception as e:
            logger.error(f"Error loading language model: {e}")

    def preprocess(self, text: str) -> str:
        """Clean and preprocess text for the model"""
        text = str(text).lower()
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        # Remove Emojis & Special characters
        text = re.sub(r'[^\w\s]', '', text)
        return text.strip()

    def check_hinglish_heuristics(self, text: str) -> bool:
        """Check if English text contains common Hindi words"""
        text_lower = text.lower()
        match_count = 0
        for word in HINGLISH_DICTIONARY:
            if re.search(rf'\b{word}\b', text_lower):
                match_count += 1
        
        return match_count >= 2

    def detect(self, text: str) -> Dict[str, Any]:
        """Detect language with confidence score"""
        if not text:
            return {"language": "Unknown", "confidence": 0.0}

        cleaned_text = self.preprocess(text)
        
        if not self.model:
            return {"language": "Basic English (Model Missing)", "confidence": 0.5}

        try:
            # Step 1: ML Prediction
            prediction = self.model.predict([cleaned_text])[0]
            probabilities = self.model.predict_proba([cleaned_text])[0]
            classes = self.model.classes_.tolist()
            
            lang_idx = classes.index(prediction)
            confidence = float(probabilities[lang_idx])

            # Step 2: Hinglish Heuristics (Refining English prediction)
            final_lang = prediction
            if prediction == "english" or prediction == "hinglish":
                if self.check_hinglish_heuristics(text):
                    final_lang = "hinglish"
                    confidence = max(confidence, 0.90) # Boost confidence for heuristic match

            # Mapping for display
            lang_map = {
                "english": "English",
                "hindi": "Hindi",
                "odia": "Odia",
                "hinglish": "Hinglish"
            }

            return {
                "language": lang_map.get(final_lang, final_lang.capitalize()),
                "confidence": round(confidence, 2)
            }

        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return {"language": "Error", "confidence": 0.0}

_detector_instance = None

def get_detector():
    """Lazy-load the Language Detector singleton."""
    global _detector_instance
    if _detector_instance is None:
        try:
            logger.info("🌍 Initializing Language Detector (Lazy Load)...")
            _detector_instance = LanguageDetector()
        except Exception as e:
            logger.error(f"❌ Failed to init Language Detector: {e}")
            return None
    return _detector_instance
