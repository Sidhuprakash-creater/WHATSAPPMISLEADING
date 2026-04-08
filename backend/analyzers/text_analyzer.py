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
    # Allow all characters (Indic/Universal) but clean extra whitespace
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


from analyzers import ollama_analyzer

async def analyze(text: str, ml_model=None) -> dict:
    """
    1. Fast Brain (ML Classifier)
    2. Deep Brain (LLM): Only invoked if ML detects suspicious content
    Returns: { label, prob, confidence, details, ollama_data }
    """
    ml_result = None
    needs_deep_analysis = False
    
    # --- STEP 1: Fast Brain (Traditional ML) ---
    if ml_model:
        try:
            clean = preprocess(text)
            if clean and len(clean.strip()) >= 3:
                prediction = ml_model.predict([clean])[0]
                probabilities = ml_model.predict_proba([clean])[0]
                classes = ml_model.classes_.tolist()
                
                pred_idx = classes.index(prediction)
                prob = float(probabilities[pred_idx])
                prob_map = {cls: round(float(p), 4) for cls, p in zip(classes, probabilities)}
                
                ml_result = {
                    "label": prediction,
                    "prob": round(prob, 4),
                    "confidence": int(prob * 100),
                    "probabilities": prob_map,
                    "details": f"ML classifier: {prediction} ({prob:.0%} confidence)",
                }
                logger.info(f"Fast Brain (ML) Output: {prediction} ({prob:.2%})")
                
                # Check if it flagged as something bad/suspicious
                if prediction.lower() in ["fake", "scam", "misleading", "toxic", "promotional", "spam"]:
                    needs_deep_analysis = True
        except Exception as e:
            logger.error(f"Text analysis ML failed: {e}")
            needs_deep_analysis = True # Fallback to LLM if ML fails
    else:
        logger.warning("ML model not loaded — routing directly to Deep Brain (LLM)")
        needs_deep_analysis = True
        
    # --- STEP 2: Deep Brain (REMOVED FOR SPEED) ---
    # Deep analysis is now centralized in llm_explainer.py to avoid redundant hangs.
    if needs_deep_analysis:
        logger.info("Suspicious or Unclear content detected. Routing to Central Explainer (Deep Brain) through Wrapper.")
        # We signal that deep analysis is needed by returning a lower confidence if needed
        # but let the wrapper handle the actual LLM call.
        if ml_result:
            ml_result["needs_llm"] = True
            return ml_result

    # --- STEP 3: Return Fast Brain Result if Deep Brain wasn't needed or failed ---
    if ml_result:
        return ml_result

    # Ultimate fallback if text was too short or both failed
    return {
        "label": "unknown",
        "prob": 0.5,
        "confidence": 50,
        "details": "Text too short or analysis unavailable",
    }
