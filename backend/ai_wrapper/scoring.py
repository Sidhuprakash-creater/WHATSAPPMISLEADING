"""
Scoring Matrix — Weighted scoring for misinformation signals
"""

# ── Scoring weights for each signal type ────────────────────
SCORING_MATRIX = {
    # ML Model signals
    "ml_fake_high": 40,  # ML → FAKE (>80% confidence)
    "ml_fake_medium": 25,  # ML → FAKE (60-80% confidence)
    "ml_misleading": 20,  # ML → MISLEADING (any confidence)
    # URL signals
    "url_malware": 35,  # Google Safe Browsing threat
    "url_domain_young": 15,  # Domain age < 7 days
    "url_virustotal": 25,  # VirusTotal flagged by 5+ engines
    "url_suspicious": 8,  # Suspicious URL pattern
    # Image signals
    "image_ai_generated": 20,  # AI-generated probability > 0.7
    "image_nsfw": 15,  # NSFW content detected
    # LLM signals
    "llm_emotional": 10,  # Emotional manipulation detected
    "llm_no_source": 10,  # No credible source found
    "llm_viral": 8,  # Viral pressure language
    "llm_conspiracy": 10,  # Conspiracy framing
    "llm_impossible": 40,  # Impossible/unverifiable high-gravity claims
    "llm_high_severity": 45,  # AI detected threat to national leaders/safety
    "llm_medium_severity": 30, # AI detected moderate misinformation or scam risk
    "web_unverified_penalty": 20,  # Penalty if no evidence found for a public figure claim
    # Positive signals (reduce score)
    "established_domain": -10,  # Domain age > 2 years
    "corroborated": -15,  # Multiple credible sources confirm
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
            ftype = finding.get("type", "")
            if ftype == "financial_scam" or ftype == "phishing_keyword":
                score += 40  # High weight for active phishing/scam intent
            else:
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
            # Handle both dict and string for robustness
            ptype = ""
            if isinstance(pattern, dict):
                ptype = pattern.get("type", "").lower()
            elif isinstance(pattern, str):
                ptype = pattern.lower()

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

        # LLM severity weighting
        severity = llm_signal.get("severity", "low").lower()
        if severity in ("high", "extreme"):
            score += SCORING_MATRIX["llm_high_severity"]
        elif severity == "medium":
            score += SCORING_MATRIX["llm_medium_severity"]

        # LLM confidence adjustment
        adjustment = llm_signal.get("llm_confidence_adjustment", 0)
        score += adjustment

    # ── Web Search Signal ───────────────────────────────
    web_signal = signals.get("web_search", {})
    if web_signal:
        status = web_signal.get("status")
        # Only apply penalty if:
        # 1. We actually performed a web search (not just default unverified), AND
        # 2. The claim was about a public figure or serious topic that needs verification
        # 3. AND the overall severity suggests this is not a safe case
        llm_signal = signals.get("llm", {})
        is_public_figure = llm_signal.get("is_public_figure", False)
        llm_severity = llm_signal.get("severity", "low").lower()

        # Only add penalty if this is actually a suspicious case (not safe)
        if (status == "unverified" or status == "not_found") and (
            is_public_figure or llm_severity in ("high", "extreme", "medium")
        ):
            score += SCORING_MATRIX["web_unverified_penalty"]

        # Public Figure Override - only if severity is high/extreme
        if (
            llm_signal.get("is_public_figure")
            and (status == "unverified" or status == "not_found")
            and llm_severity in ("high", "extreme")
        ):
            print(
                f"DEBUG: [Public Figure Override Triggered] for {llm_signal.get('primary_claim')}"
            )
            score = max(score, 88)

    # ── IndicBERT Context Signal ────────────────────────
    indic_signal = signals.get("indic_context", {})
    if indic_signal:
        adjustment = indic_signal.get("indic_risk_adjustment", 0)
        score += adjustment
        if adjustment < 0:
            print(f"DEBUG: [IndicBERT Safe Context Adjustment] -> {adjustment}")

    # ── CRITICAL OVERRIDE: Mortality & High-Stakes Logic ────────
    # If LLM detects Extreme risk (Death, Murder, etc.), override all safe signals
    llm_signal = signals.get("llm", {})
    llm_severity = llm_signal.get("severity", "low").lower()
    
    # Check for mortality/morbidity in messages specifically
    is_morbidity = any("death" in str(p).lower() or "murder" in str(p).lower() or "morbidity" in str(p).lower() 
                       for p in llm_signal.get("patterns_found", []))
    
    if llm_severity == "extreme" or (llm_severity == "high" and is_morbidity):
        print(f"DEBUG: [!!! CRITICAL MORTALITY OVERRIDE TRIGGERED !!!] -> Severity: {llm_severity}")
        score = max(score, 98)

    print(f"DEBUG: [Final Risk Score Computed] -> {score}")
    # Clamp to 0-100
    return max(0, min(100, int(score)))


def get_verdict(score: int) -> str:
    """Convert score to verdict string"""
    if score >= 60:
        return "High Risk"
    elif score >= 30:
        return "Medium Risk"
    else:
        return "Low Risk"
