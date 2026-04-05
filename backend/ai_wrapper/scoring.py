"""
Scoring Matrix — Weighted scoring for misinformation signals
"""


# ── Scoring weights for each signal type ────────────────────
SCORING_MATRIX = {
    # ML Model signals
    "ml_fake_high":      40,    # ML → FAKE (>80% confidence)
    "ml_fake_medium":    25,    # ML → FAKE (60-80% confidence)
    "ml_misleading":     20,    # ML → MISLEADING (any confidence)
    
    # URL signals
    "url_malware":       35,    # Google Safe Browsing threat
    "url_domain_young":  15,    # Domain age < 7 days
    "url_virustotal":    25,    # VirusTotal flagged by 5+ engines
    "url_suspicious":     8,    # Suspicious URL pattern
    
    # Image signals
    "image_ai_generated": 20,   # AI-generated probability > 0.7
    "image_nsfw":        15,    # NSFW content detected
    
    # LLM signals
    "llm_emotional":     10,    # Emotional manipulation detected
    "llm_no_source":     10,    # No credible source found
    "llm_viral":          8,    # Viral pressure language
    "llm_conspiracy":    10,    # Conspiracy framing
    "llm_impossible":    12,    # Impossible/unverifiable claims
    
    # Positive signals (reduce score)
    "established_domain": -10,  # Domain age > 2 years
    "corroborated":      -15,   # Multiple credible sources confirm
}


def compute_score(signals: dict) -> int:
    """
    Compute risk score from all analyzer signals.
    Returns score 0-100.
    """
    score = 0
    
    # ── ML Model Signals ────────────────────────────────
    text_signal = signals.get("text", {})
    if text_signal:
        label = text_signal.get("label", "")
        prob = text_signal.get("prob", 0)
        
        if label == "fake":
            if prob > 0.80:
                score += SCORING_MATRIX["ml_fake_high"]
            elif prob > 0.60:
                score += SCORING_MATRIX["ml_fake_medium"]
        elif label == "misleading":
            score += SCORING_MATRIX["ml_misleading"]
    
    # ── URL Signals ─────────────────────────────────────
    url_signal = signals.get("url", {})
    if url_signal:
        if url_signal.get("threat"):
            score += SCORING_MATRIX["url_malware"]
        
        findings = url_signal.get("findings", [])
        for finding in findings:
            score += SCORING_MATRIX.get("url_suspicious", 8)
    
    # ── Image Signals ───────────────────────────────────
    image_signal = signals.get("image", {})
    if image_signal:
        if image_signal.get("ai_generated", 0) > 0.7:
            score += SCORING_MATRIX["image_ai_generated"]
        if image_signal.get("nsfw"):
            score += SCORING_MATRIX["image_nsfw"]
    
    # ── LLM Signals ─────────────────────────────────────
    llm_signal = signals.get("llm", {})
    if llm_signal:
        patterns = llm_signal.get("patterns_found", [])
        for pattern in patterns:
            ptype = pattern.get("type", "")
            if "emotional" in ptype or "manipulation" in ptype:
                score += SCORING_MATRIX["llm_emotional"]
            elif "source" in ptype or "no_source" in ptype:
                score += SCORING_MATRIX["llm_no_source"]
            elif "viral" in ptype:
                score += SCORING_MATRIX["llm_viral"]
            elif "conspiracy" in ptype:
                score += SCORING_MATRIX["llm_conspiracy"]
            elif "impossible" in ptype or "unverifiable" in ptype:
                score += SCORING_MATRIX["llm_impossible"]
        
        # LLM confidence adjustment
        adjustment = llm_signal.get("llm_confidence_adjustment", 0)
        score += adjustment
    
    # Clamp to 0-100
    return max(0, min(100, score))


def get_verdict(score: int) -> str:
    """Convert score to verdict string"""
    if score >= 60:
        return "High Risk"
    elif score >= 30:
        return "Medium Risk"
    else:
        return "Low Risk"
