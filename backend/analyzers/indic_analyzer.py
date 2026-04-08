import aiohttp
import json
import logging
import re

logger = logging.getLogger(__name__)

# Instant Regex Fast-Pass (0ms reasoning) for regional greetings/safe verbs
REGIONAL_SAFE_PATTERNS = [
    r"\b(salam|namaste|kemiti achu|kemicho|khabar kana|jay jagannath)\b",
    r"\b(good morning|suprabhat|subha sakala|suvasankhya)\b",
    r"\b(happy birthday|janmadina ra shubhechha|mubarak)\b",
    r"\b(kana karuchu|kya kar rahe ho|what are you doing)\b",
    r"\b(khana khaya|khai dela ki|did you eat)\b"
]

class IndicAnalyzer:
    def __init__(self, ollama_url="http://localhost:11434/api/generate"):
        self.ollama_url = ollama_url
        self.model = "llama3.1:latest"

    async def analyze_context(self, text: str) -> dict:
        """
        Multilingual Context Gatekeeper.
        Priority 1: Instant Regex Pattern (Odia/Hinglish Verbs)
        Priority 2: Local LLM Deep Context (Ollama)
        """
        import unicodedata
        text_norm = unicodedata.normalize('NFKC', text.lower().strip())
        
        # ── PRIORITY 0: Critical Keyword Shield (Death/Murder) ─────────────
        # Prevent "Safe Pass" for rumors involving death, murder, or violence
        CRITICAL_KEYWORDS = [
            'death', 'murder', 'kill', 'attack', 'accident', 'dead', 'shradhanjali',
            'maut', 'mar diya', 'mar gaya', 'hatya', 'badla', 'dhamki', 'bomb',
            'blast', 'terrorism', 'arrest', 'scam', 'prize', 'lottery', 'winner'
        ]
        if any(kw in text_norm for kw in CRITICAL_KEYWORDS):
            logger.info("⚠️ Critical Keywords Detected — Skipping Fast-Pass and forcing deep analysis.")
            return {"indic_risk_adjustment": 5, "reason": "Critical keywords detected — skipping fast-pass.", "intent": "critical"}

        # ── PRIORITY 1: Instant Regex Pass (0ms) ──────────────────────────
        for pattern in REGIONAL_SAFE_PATTERNS:
            if re.search(pattern, text_norm):
                logger.info(f"✅ Instant Regio-Safe Match: '{pattern}' detected in '{text}'")
                return {
                    "indic_risk_adjustment": -35, # Strong reduction to ensure it becomes Safe
                    "reason": "Harmless regional verb/greeting detected (Instant-Pass)",
                    "intent": "safe",
                    "engine": "regex_fast_pass"
                }

        # ── PRIORITY 2: Deep Context (REMOVED FOR SPEED) ───────────────────
        # Deep context analysis is now handled by the central Cloud LLM (Groq)
        # in llm_explainer.py to avoid local hangs.
        return {"indic_risk_adjustment": 0, "reason": "No instant regional match"}

_indic_engine = None

def get_indic_engine():
    """Lazy-load Indic Analyzer singleton."""
    global _indic_engine
    if _indic_engine is None:
        _indic_engine = IndicAnalyzer()
    return _indic_engine
