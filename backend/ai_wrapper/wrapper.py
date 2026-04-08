"""
AI Wrapper — The Orchestrator (v3 — Groq-Primary Pipeline)
===========================================================
Pipeline:
  1. Detect language
  2. Extract any URLs from text
  3. Run URL security scan (Google Safe Browsing + VirusTotal) in parallel with language detection
  4. Call Groq LLM with FULL context (text + URL scan results) → primary verdict
  5. Compute final score from Groq severity + URL scores
  6. Return rich structured result

ML MODEL: LOCKED (kept in code, bypassed in pipeline)
"""

import asyncio
import json
import logging
import os
import re

from ai_wrapper.llm_explainer import explain, detect_language
from ai_wrapper.semantic_logic import get_memory
from analyzers import url_analyzer, fact_checker, claim_extractor, image_analyzer, apk_analyzer

logger = logging.getLogger(__name__)

# ── ML MODEL: LOCKED ──────────────────────────────────────────────────────
# The sklearn ML model is intentionally bypassed.
# Groq LLM is the sole decision-maker for all text analysis.
ML_MODEL_LOCKED = True


# ── Persistent Cache ──────────────────────────────────────────────────────
class PersistentCache:
    def __init__(self, filename="analysis_cache.json"):
        self.filename = os.path.join(os.path.dirname(__file__), "..", "data", filename)
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        self.cache = self._load()

    def _load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self):
        try:
            with open(self.filename, "w") as f:
                json.dump(self.cache, f)
        except Exception:
            pass

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        self.cache[key] = value
        self._save()


analysis_cache = PersistentCache()


# ── Bootstrap Semantic Memory (MOVED TO LAZY) ─────────────────────────────
# Removed from top-level to prevent blocking uvicorn startup.
# Bootstrapping now happens inside get_memory() if needed or skipped for speed.


# ── Score Calculator (Groq-primary) ──────────────────────────────────────
def _compute_score_from_groq(llm_result: dict, url_scan: dict = None) -> int:
    """
    Derives a 0-100 risk score from Groq's severity + URL scan results.
    The ML model is locked, so no ML scores are used.
    """
    severity = llm_result.get("severity", "low").lower()
    adjustment = llm_result.get("llm_confidence_adjustment", 0)

    base_score = {
        "extreme": 92,
        "high": 72,
        "medium": 42,
        "low": 12,
        "safe": 5,
    }.get(severity, 12)

    base_score += adjustment

    # Boost from URL scan
    if url_scan:
        gsb = url_scan.get("google_safe_browsing", {})
        vt = url_scan.get("virustotal", {})
        heuristics = url_scan.get("heuristic_findings", [])

        if gsb.get("checked") and not gsb.get("safe"):
            base_score = max(base_score, 85)  # Confirmed GSB threat → always high risk

        vt_malicious = vt.get("malicious", 0) if isinstance(vt, dict) else 0
        if vt_malicious >= 3:
            base_score = max(base_score, 80)
        elif vt_malicious >= 1:
            base_score += 15

        base_score += len(heuristics) * 8

    return max(0, min(100, int(base_score)))


def _get_verdict(score: int) -> str:
    if score >= 60:
        return "High Risk"
    elif score >= 30:
        return "Medium Risk"
    return "Low Risk"


# ── Rich Explanation Builder ──────────────────────────────────────────────
def _build_rich_explanation(llm_result: dict, url_scan: dict, risk_score: int, media_scan: dict = None) -> dict:
    """
    Assembles the full structured explanation object for the Flutter UI.
    Every field comes from real Groq analysis or live API results.
    """
    is_safe = risk_score < 30

    # Build verified sources from claim_vs_reality source hints
    verified_sources = []
    for cr in llm_result.get("claim_vs_reality", []):
        hint = cr.get("source_hint", "")
        if hint:
            for src in hint.split(","):
                src = src.strip()
                if src and not any(s["title"] == src for s in verified_sources):
                    verified_sources.append({
                        "title": src,
                        "url": f"https://{src}" if not src.startswith("http") else src,
                    })

    # Add URL scan sources
    if url_scan:
        gsb = url_scan.get("google_safe_browsing", {})
        vt = url_scan.get("virustotal", {})
        if gsb.get("checked"):
            verified_sources.append({
                "title": f"Google Safe Browsing: {gsb.get('verdict', 'Checked')}",
                "url": "https://safebrowsing.google.com",
            })
        if vt.get("checked"):
            verified_sources.append({
                "title": f"VirusTotal: {vt.get('verdict', 'Checked')}",
                "url": "https://www.virustotal.com",
            })

    # Build real_vs_fake_data string from URL scan
    real_vs_fake_data = ""
    if url_scan:
        real_vs_fake_data = url_scan.get("summary", "")

    # For safe messages, clear the scary content
    if is_safe:
        return {
            "summary": "No suspicious patterns detected. This appears to be a safe message.",
            "primary_claim": llm_result.get("primary_claim", ""),
            "why_fake": ["No misinformation patterns found."],
            "entities": [],
            "claim_vs_reality": [],
            "patterns_found": [],
            "real_vs_fake_data": "",
            "verified_sources": [],
            "safe_to_forward": True,
            "url_security": url_scan or {},
            "is_ai_generated": media_scan.get("ai_generated", 0) > 80 if media_scan else False,
            "is_nsfw": media_scan.get("nsfw", False) if media_scan else False,
            "media_scan_details": media_scan.get("details", "") if media_scan else "",
            "media_scan_analysis": media_scan.get("analysis", {}) if media_scan else {},
        }

    return {
        "summary": llm_result.get("summary", ""),
        "primary_claim": llm_result.get("primary_claim", ""),
        "why_fake": llm_result.get("why_fake", []),
        "entities": llm_result.get("entities", []),
        "claim_vs_reality": llm_result.get("claim_vs_reality", []),
        "patterns_found": llm_result.get("patterns_found", []),
        "real_vs_fake_data": real_vs_fake_data,
        "verified_sources": verified_sources,
        "safe_to_forward": llm_result.get("safe_to_forward", False),
        "url_security": url_scan or {},
        "url_security_summary": llm_result.get("url_security_summary", ""),
        "is_ai_generated": media_scan.get("ai_generated", 0) > 80 if media_scan else False,
        "is_nsfw": media_scan.get("nsfw", False) if media_scan else False,
        "media_scan_details": media_scan.get("details", "") if media_scan else "",
        "media_scan_analysis": media_scan.get("analysis", {}) if media_scan else {},
    }


def _simple_reasons(llm_result: dict, url_scan: dict, risk_score: int, media_scan: dict = None) -> list[str]:
    """Flat reasons list for backward compatibility with the API response."""
    reasons = []
    is_safe = risk_score < 30

    if is_safe:
        return ["No suspicious patterns detected."]

    # From Groq patterns
    for p in llm_result.get("patterns_found", [])[:3]:
        if isinstance(p, dict):
            ptype = p.get("type", "")
            evidence = p.get("evidence", "")
            if ptype and evidence:
                reasons.append(f"{ptype}: {evidence[:100]}")
        elif isinstance(p, str):
            reasons.append(p[:100])

    # From Groq why_fake
    for r in llm_result.get("why_fake", [])[:3]:
        if isinstance(r, str) and len(r) > 10 and r not in reasons:
            reasons.append(r[:200])

    # From URL scan
    if url_scan:
        gsb = url_scan.get("google_safe_browsing", {})
        vt = url_scan.get("virustotal", {})
        if gsb.get("checked") and not gsb.get("safe"):
            reasons.append(f"Google Safe Browsing: {gsb.get('verdict', 'Threat detected')}")
        if isinstance(vt, dict) and vt.get("malicious", 0) >= 1:
            reasons.append(f"VirusTotal: {vt.get('verdict', 'Malicious detected')}")

    # From Media Scan
    if media_scan:
        if media_scan.get("ai_generated", 0) > 80:
            reasons.append("AI-Generated visual artifacts detected.")
        for sign in media_scan.get("analysis", {}).get("manipulation_signs", [])[:2]:
            reasons.append(sign)

    if not reasons:
        reasons.append("Potential misinformation detected — review before sharing.")

    return list(dict.fromkeys(reasons))[:8]


# ── CRITICAL bypass keywords (always force fresh Groq analysis) ───────────
CRITICAL_BYPASS_WORDS = [
    "death", "dead", "murder", "kill", "maut", "mar gaya", "hatya",
    "scam", "prize", "lottery", "winner", "reward", "cash", "click",
    "arrested", "blast", "attack", "bomb", "rape", "riot",
]


def _is_critical(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in CRITICAL_BYPASS_WORDS)


# ── MAIN PIPELINE ────────────────────────────────────────────────────────
async def run_full_analysis(input_data: dict) -> dict:
    """
    v3 Groq-Primary Pipeline (Optimized for Extreme Speed):
    - Parallel Group 1: URL Detection, Language, Media Scan, Claim Extraction
    - Parallel Group 2: Fact Checking (depends on Claims)
    - Sequential final step: Groq Master Reasoning
    """
    text = input_data.get("text", "") or ""
    content_type = input_data.get("content_type", "text")
    file_url = input_data.get("file_url")
    explicit_url = input_data.get("url")

    # ── Step 0: Fast Cache Check ──────────────────────────────────────────
    is_critical = _is_critical(text)
    import hashlib
    cache_key = f"v4:{content_type}:{text[:200]}"
    if file_url:
        cache_key += f":{hashlib.md5(file_url.encode('utf-8')).hexdigest()}"
    if not is_critical:
        cached = await asyncio.to_thread(analysis_cache.get, cache_key)
        if cached:
            logger.info("[Pipeline] Cache HIT — returning instant result")
            return cached
        
        mem = get_memory()
        similar = await asyncio.to_thread(mem.find_similar, text) if (text and mem) else None
        if similar:
            logger.info("[Pipeline] Semantic match — returning similar result")
            return similar

    logger.info(f"[Pipeline] Starting Dynamic Parallel Analysis... (Critical={is_critical})")

    # ── Step 1: Context Gathering (PARALLEL GROUP 1) ──────────────────────
    # We trigger EVERYTHING that doesn't depend on each other at once.
    
    # Task A: URL Detection & Analysis
    async def get_url_scan():
        url_pattern = re.compile(r"https?://[^\s<>\"]+|www\.[^\s<>\"]+", re.IGNORECASE)
        found_urls = url_pattern.findall(text)
        if explicit_url and explicit_url not in found_urls:
            found_urls.insert(0, explicit_url)
        
        if not found_urls:
            return None, []
            
        primary_url = found_urls[0]
        try:
            res = await asyncio.wait_for(url_analyzer.analyze(primary_url), timeout=12.0)
            return res, found_urls
        except Exception as e:
            logger.warning(f"[Pipeline] URL scan skipped: {e}")
            return None, found_urls

    # Task B: Media Analysis
    async def get_media_scan():
        if not file_url:
            return None
        try:
            if content_type == "image":
                return await asyncio.wait_for(image_analyzer.analyze(file_url), timeout=80.0)
            elif content_type == "document":
                return await asyncio.wait_for(apk_analyzer.analyze(file_url), timeout=80.0)
        except Exception as e:
            logger.warning(f"[Pipeline] Media scan skipped: {e}")
        return None

    # Trigger Group 1
    logger.info("[Pipeline] Group 1 starting: Language, URLs, Media, Claims...")
    
    async def safe_extract_claims(t):
        try:
            return await asyncio.wait_for(claim_extractor.extract_claims(t), timeout=10.0)
        except Exception as e:
            logger.warning(f"[Pipeline] Claim extraction timed out or failed: {e}")
            return []

    tasks = [
        asyncio.create_task(asyncio.to_thread(detect_language, text)),
        asyncio.create_task(get_url_scan()),
        asyncio.create_task(get_media_scan()),
        asyncio.create_task(safe_extract_claims(text))
    ]
    
    # Wait for initial data with a safeguard timeout for the entire group
    try:
        results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=85.0)
    except asyncio.TimeoutError:
        logger.error("[Pipeline] Parallel Group 1 CRITICAL TIMEOUT — force continuing with partials")
        results = ["english", (None, []), None, []] # Defaults
    
    detected_lang = results[0] if not isinstance(results[0], Exception) else "english"
    url_scan_result, found_urls = results[1] if not isinstance(results[1], Exception) else (None, [])
    media_scan_result = results[2] if not isinstance(results[2], Exception) else None
    claims = results[3] if not isinstance(results[3], Exception) else []

    # ── Step 2: Verification (PARALLEL GROUP 2) ───────────────────────────
    # This depends on Level 1 Claims.
    fact_check_results = []
    if claims:
        logger.info(f"[Pipeline] Parallel Fact-Checking for {len(claims)} claims...")
        verification_tasks = [
            fact_checker.engine.check_claims(claims),        # Local FAISS
            fact_checker.engine.check_online_claims(claims)  # Web Search (it's already parallelized inside)
        ]
        v_results = await asyncio.gather(*verification_tasks, return_exceptions=True)
        for vr in v_results:
            if isinstance(vr, list):
                fact_check_results.extend(vr)

    # ── Step 3: Master Reasoning ──────────────────────────────────────────
    logger.info("[Pipeline] Final step: MASTER Groq reasoning...")
    llm_result = {}
    try:
        llm_result = await asyncio.wait_for(
            explain(
                text=text,
                url_scan_results=url_scan_result,
                fact_check_results=fact_check_results,
                detected_lang=detected_lang,
            ),
            timeout=25.0, # Strict deadline
        )
    except Exception as e:
        logger.error(f"[Pipeline] Groq failure: {e}")
        from ai_wrapper.llm_explainer import _fallback_result
        llm_result = _fallback_result(str(e))

    # ── Step 4: Scoring & Assembly ────────────────────────────────────────
    risk_score = _compute_score_from_groq(llm_result, url_scan_result)
    
    # Media score override logic
    if media_scan_result and media_scan_result.get("score", 0) > 0:
        media_score = media_scan_result.get("score", 0)
        if media_scan_result.get("nsfw", False) or media_scan_result.get("ai_generated", 0) > 25 or media_score >= 40:
            risk_score = max(risk_score, media_score)
        else:
            risk_score = max(risk_score, min(media_score, 25))


    logger.info(
        f"[Pipeline] Done | severity={llm_result.get('severity')} | "
        f"score={risk_score} | urls_found={len(found_urls)}"
    )

    # ── Step 7: Assemble Final Result ────────────────────────────────────
    rich_explanation = _build_rich_explanation(llm_result, url_scan_result, int(risk_score), media_scan_result or {})
    reasons = _simple_reasons(llm_result, url_scan_result, int(risk_score), media_scan_result or {})

    # Force Integer/Float types for Pydantic 2 strictness
    final_risk_score = int(risk_score)
    final_confidence = int(risk_score) # Use risk_score as confidence for now

    final_result = {
        "verdict": _get_verdict(final_risk_score),
        "confidence": final_confidence,
        "risk_score": final_risk_score,
        "reasons": reasons,
        "explanation": rich_explanation,
        "signals": {
            "llm": llm_result or {},
            "url": url_scan_result or {},
            "media": media_scan_result or {},
            "ml_locked": bool(ML_MODEL_LOCKED),
            "_detected_lang": str(detected_lang),
        },
    }

    # ── Step 8: Cache (only non-timeout results) ─────────────────────────
    if not llm_result.get("is_timeout"):
        analysis_cache.set(cache_key, final_result)
        mem = get_memory()
        if text and mem:
            asyncio.create_task(asyncio.to_thread(mem.add_to_memory, text, final_result))
    else:
        logger.info("[Pipeline] Timeout result — not caching")

    return final_result
