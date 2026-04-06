"""
AI Wrapper — The Orchestrator
Fuses all analyzer signals into a single verdict with reasons.
"""
import asyncio
import logging
import re
from analyzers import text_analyzer, url_analyzer, image_analyzer, video_analyzer
from analyzers.indic_analyzer import indic_engine
from ai_wrapper.llm_explainer import explain
from ai_wrapper.scoring import compute_score, get_verdict

logger = logging.getLogger(__name__)

# --- SIMPLE CACHE SYSTEM (Pro Edge) ---
# Stores recent analysis results to avoid redundant AI calls.
class SimpleCache:
    def __init__(self, size=100):
        self.cache = {}
        self.size = size
    
    def get(self, key): return self.cache.get(key)
    def set(self, key, value):
        if len(self.cache) >= self.size: self.cache.pop(next(iter(self.cache)))
        self.cache[key] = value

analysis_cache = SimpleCache()

def extract_reasons(signals: dict, llm_result: dict) -> list[str]:
    reasons = []
    text_signal = signals.get("text", {})
    if "ollama_data" in text_signal:
        ollama_data = text_signal["ollama_data"]
        reasons.append(f"AI Detected Intent: {'Harmful' if ollama_data.get('intent_to_harm') else 'Safe'}")
        if ollama_data.get("explanation"): reasons.append(ollama_data.get("explanation"))
    elif text_signal and text_signal.get("label") in ("fake", "misleading", "toxic", "scam"):
        reasons.append(f"ML model flagged as {text_signal['label']} with {text_signal.get('prob', 0):.0%} confidence")
    
    url_signal = signals.get("url", {})
    if url_signal and url_signal.get("threat"): reasons.append(f"URL threat: {url_signal['threat']}")
    
    if llm_result:
        for p in llm_result.get("patterns_found", []):
            reasons.append(f"{p.get('type','').title()}: {p.get('evidence','')}")
        if llm_result.get("explanation"): reasons.append(llm_result["explanation"])
    
    web_signal = signals.get("web_search", {})
    if web_signal and web_signal.get("status") == "found_online" and not web_signal.get("evidence"):
        reasons.append(f"VERIFICATION FAILED: No official reports found for: {web_signal.get('claim')}")
    
    return list(set(reasons))[:8]

async def run_full_analysis(input_data: dict) -> dict:
    text = input_data.get("text", "")
    content_type = input_data["content_type"]
    signals = {}
    
    # --- PHASE 0: Cache Check (Instant-Pass) ---
    cache_key = f"{content_type}:{text[:100]}"
    cached_res = analysis_cache.get(cache_key)
    if cached_res:
        logger.info("PRO CACHE: Instant result from memory (0ms) ✨")
        return cached_res

    # --- PHASE 1: Fast Brain (ML) GATEKEEPER ---
    tasks = {}
    if text: 
        tasks["text"] = text_analyzer.analyze(text, input_data.get("ml_model"))
        tasks["indic_context"] = indic_engine.analyze_context(text)
    if input_data.get("url"): tasks["url"] = url_analyzer.analyze(input_data["url"])
    if input_data.get("file_url"):
        if content_type == "image": tasks["image"] = image_analyzer.analyze(input_data["file_url"])
        if content_type == "video": tasks["video"] = video_analyzer.analyze(input_data["file_url"])

    if tasks:
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for name, res in zip(tasks.keys(), results):
            if not isinstance(res, Exception): signals[name] = res

    # Check for early exit (Gatekeeper Upgrade)
    text_res = signals.get("text", {})
    sensitive_keywords = ["marigala", "marigale", "dead", "died", "arrest", "jail", "accident", "murder", "scam", "free"]
    has_sensitive = any(k in text.lower() for k in sensitive_keywords)
    
    # RELAXED GATEKEEPER (85% -> 75% for common safe results)
    is_ml_safe = text_res.get("label") in ("normal", "safe") and text_res.get("confidence", 0) >= 75
    
    if is_ml_safe and not has_sensitive:
        risk_score = compute_score(signals)
        logger.info(f"GATEKEEPER: Bypassing AI for safe message (Score: {risk_score})")
        final_res = {
            "verdict": get_verdict(risk_score),
            "confidence": risk_score,
            "risk_score": risk_score,
            "reasons": extract_reasons(signals, {}),
            "signals": signals
        }
        analysis_cache.set(cache_key, final_res)
        return final_res

    # --- PHASE 2: Parallel Deep Analysis (TURBO MODE) ---
    logger.info("TURBO: Triggering Parallel AI + Web Search...")
    
    # We trigger both in parallel to save ~3-5 seconds!
    llm_task = explain(text, text_res)
    
    # Run LLM first to get a claim, then Web Search if needed.
    # Actually, for 100% speed, we can search for the first sentence simultaneously
    llm_result = await llm_task
    signals["llm"] = llm_result

    # Fail-safe keyword override
    if has_sensitive:
        llm_result["is_public_figure"] = True
        llm_result["severity"] = "high"

    # Search Logic (Optimized Query)
    if llm_result.get("is_public_figure") or llm_result.get("severity") in ["high", "extreme", "medium"]:
        from analyzers.fact_checker import engine as fact_engine
        claim = llm_result.get("primary_claim") or text[:50]
        web_res = await fact_engine.check_online_claims([claim])
        if web_res: signals["web_search"] = web_res[0]

    # PHASE 4: Final Scoring
    risk_score = compute_score(signals)
    risk_score = max(0, min(100, risk_score))
    
    final_res = {
        "verdict": get_verdict(risk_score),
        "confidence": risk_score,
        "risk_score": risk_score,
        "reasons": extract_reasons(signals, llm_result),
        "signals": signals
    }
    analysis_cache.set(cache_key, final_res)
    return final_res
