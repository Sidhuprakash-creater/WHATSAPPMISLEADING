"""
Text Analyzer — Tier 1 (Fast Brain)
Uses TF-IDF + Logistic Regression for instant classification
"""
import re
import logging

logger = logging.getLogger(__name__)


def preprocess(text: str) -> str:
    """Clean text for ML model input"""
    text = str(text).lower()
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'[^a-z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


async def analyze(text: str, ml_model=None) -> dict:
    """
    Run text through ML classifier.
    Returns: { label, prob, confidence, details }
    """
    if not ml_model:
        logger.warning("ML model not loaded — returning neutral result")
        return {
            "label": "unknown",
            "prob": 0.5,
            "confidence": 50,
            "details": "ML model not available",
        }
    
    try:
        clean = preprocess(text)
        
        if not clean or len(clean.strip()) < 3:
            return {
                "label": "unknown",
                "prob": 0.5,
                "confidence": 50,
                "details": "Text too short for analysis",
            }
        
        # Predict
        prediction = ml_model.predict([clean])[0]
        probabilities = ml_model.predict_proba([clean])[0]
        classes = ml_model.classes_.tolist()
        
        # Get probability for predicted class
        pred_idx = classes.index(prediction)
        prob = float(probabilities[pred_idx])
        
        # Build probability map
        prob_map = {cls: round(float(p), 4) for cls, p in zip(classes, probabilities)}
        
        result = {
            "label": prediction,
            "prob": round(prob, 4),
            "confidence": int(prob * 100),
            "probabilities": prob_map,
            "details": f"ML classifier: {prediction} ({prob:.0%} confidence)",
        }
        
        logger.info(f"Text analysis: {prediction} ({prob:.2%})")
        return result
        
    except Exception as e:
        logger.error(f"Text analysis failed: {e}")
        return {
            "label": "error",
            "prob": 0.0,
            "confidence": 0,
            "details": f"Analysis error: {str(e)}",
        }
