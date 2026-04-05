"""
AI Wrapper — The Orchestrator (Tier 3)
Fuses all analyzer signals into a single verdict with reasons.
This is the most important component in the system.
"""
import asyncio
import logging
from analyzers import text_analyzer, url_analyzer, image_analyzer, video_analyzer
from ai_wrapper.llm_explainer import explain
from ai_wrapper.scoring import compute_score, get_verdict

logger = logging.getLogger(__name__)


def extract_reasons(signals: dict, llm_result: dict) -> list[str]:
    """
    Extract human-readable reasons from all signals.
    These are shown to the user as bullet points.
    """
    reasons = []
    
    # ── ML Model reasons ────────────────────────────────
    text_signal = signals.get("text", {})
    if text_signal and text_signal.get("label") in ("fake", "misleading"):
        label = text_signal["label"]
        prob = text_signal.get("prob", 0)
        reasons.append(
            f"ML model flagged as {label} with {prob:.0%} confidence"
        )
    
    # ── URL reasons ─────────────────────────────────────
    url_signal = signals.get("url", {})
    if url_signal:
        if url_signal.get("threat"):
            reasons.append(
                f"URL security threat detected: {url_signal['threat']}"
            )
        for finding in url_signal.get("findings", []):
            reasons.append(finding.get("evidence", "Suspicious URL pattern"))
    
    # ── Image reasons ───────────────────────────────────
    image_signal = signals.get("image", {})
    if image_signal and image_signal.get("analyzed"):
        ai_gen = image_signal.get("ai_generated", 0)
        if ai_gen > 0.7:
            reasons.append(
                f"Image appears to be AI-generated ({ai_gen:.0%} probability)"
            )
        analysis = image_signal.get("analysis", {})
        for trigger in analysis.get("emotional_triggers", []):
            reasons.append(f"Image emotional trigger: {trigger}")
    
    # ── LLM reasons ─────────────────────────────────────
    if llm_result:
        for pattern in llm_result.get("patterns_found", []):
            ptype = pattern.get("type", "").replace("_", " ").title()
            evidence = pattern.get("evidence", "")
            reasons.append(f"{ptype}: {evidence}")
        
        explanation = llm_result.get("explanation", "")
        if explanation and explanation not in reasons:
            reasons.append(explanation)
    
    # Deduplicate and limit
    seen = set()
    unique_reasons = []
    for r in reasons:
        if r not in seen:
            seen.add(r)
            unique_reasons.append(r)
    
    return unique_reasons[:8]  # Max 8 reasons


async def run_full_analysis(input_data: dict) -> dict:
    """
    Main orchestration function.
    Runs all relevant analyzers in parallel, fuses scores, generates verdict.
    
    Args:
        input_data: {
            content_type: str,
            text: str | None,
            url: str | None,
            file_url: str | None,
            ml_model: object | None,
        }
    
    Returns:
        { verdict, confidence, risk_score, reasons, signals }
    """
    content_type = input_data["content_type"]
    signals = {}
    
    # ── Step 1: Run relevant analyzers in PARALLEL ──────
    tasks = {}
    
    if content_type in ("text", "url") and input_data.get("text"):
        tasks["text"] = text_analyzer.analyze(
            input_data["text"], 
            input_data.get("ml_model")
        )
    
    if content_type == "url" and input_data.get("url"):
        tasks["url"] = url_analyzer.analyze(input_data["url"])
    
    if content_type == "image" and input_data.get("file_url"):
        tasks["image"] = image_analyzer.analyze(input_data["file_url"])
    
    if content_type == "video" and input_data.get("file_url"):
        tasks["video"] = video_analyzer.analyze(input_data["file_url"])
    
    # Run all analyzers concurrently
    if tasks:
        task_names = list(tasks.keys())
        results = await asyncio.gather(
            *tasks.values(), 
            return_exceptions=True
        )
        
        for name, result in zip(task_names, results):
            if isinstance(result, Exception):
                logger.error(f"Analyzer {name} failed: {result}")
                signals[name] = {"error": str(result)}
            else:
                signals[name] = result
    
    # ── Step 2: Compute initial score ───────────────────
    risk_score = compute_score(signals)
    
    # ── Step 3: LLM enrichment (if score > 30 or text content) ──
    llm_result = {}
    if input_data.get("text") and (risk_score > 30 or content_type == "text"):
        ml_result = signals.get("text", {"label": "unknown", "prob": 0.5})
        llm_result = await explain(input_data["text"], ml_result)
        signals["llm"] = llm_result
        
        # Recompute score with LLM signals
        risk_score = compute_score(signals)
    
    # ── Step 4: Final verdict ───────────────────────────
    risk_score = max(0, min(100, risk_score))
    verdict = get_verdict(risk_score)
    reasons = extract_reasons(signals, llm_result)
    
    logger.info(f"Analysis complete: {verdict} (score: {risk_score})")
    
    return {
        "verdict": verdict,
        "confidence": risk_score,
        "risk_score": risk_score,
        "reasons": reasons,
        "signals": signals,
    }
