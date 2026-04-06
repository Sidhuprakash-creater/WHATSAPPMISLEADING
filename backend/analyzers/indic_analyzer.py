import aiohttp
import json
import logging
import re

logger = logging.getLogger(__name__)

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
        text_lower = text.lower().strip()
        
        # ── PRIORITY 1: Instant Regex Pass (0ms) ──────────────────────────
        # Added 50+ common harmless Odia and Hinglish verbs to avoid AI overhead
        REGIONAL_SAFE_PATTERNS = [
            # Odia Safe Verbs (Transliterated)
            r"\bhei\s*gala\b", r"\bkha\w*\s*gala\b", r"\bsoi\s*gala\b", r"\bjai\s*gala\b",
            r"\braki\s*gala\b", r"\bkhoji\s*gala\b", r"\blekhili\b", r"\bdekhili\b",
            r"\bpadhili\b", r"\bkhaichi\b", r"\bsoichi\b", r"\bjaochi\b", r"\brakhuchi\b",
            r"\bkheluchi\b", r"\bhasuchi\b", r"\bkanduchi\b", r"\bkaruchi\b", r"\bbasuchi\b",
            r"\buthuchi\b", r"\bdhaunuchi\b", r"\bpauchi\b", r"\baasigala\b", r"\brahigala\b",
            r"\bferigala\b", r"\bkahuchi\b", r"\bsunuchi\b", r"\bdekhuchi\b", r"\bkhauchi\b",
            
            # Hinglish Safe Verbs
            r"\bho\s*gaya\b", r"\bkha\s*liya\b", r"\bso\s*gaya\b", r"\bjaa\s*raha\b",
            r"\bbaat\s*kar\b", r"\bdekh\s*liya\b", r"\bsun\s*liya\b", r"\bpadh\s*liya\b",
            r"\bmil\s*gaya\b", r"\baa\s*gaya\b", r"\bchala\s*gaya\b", r"\brakh\s*liya\b",
            r"\bbhej\s*diya\b", r"\bkar\s*diya\b", r"\blikh\s*liya\b", r"\bsamajh\s*gaya\b",
            r"\bkha\s*rha\b", r"\bpee\s*liya\b", r"\bgaya\s*tha\b", r"\baaya\s*tha\b",
            
            # Greetings/Common
            r"kemiti\s*achha", r"namaskar", r"suva\s*sakal"
        ]
        
        for pattern in REGIONAL_SAFE_PATTERNS:
            if re.search(pattern, text_lower):
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

# Global Instance
indic_engine = IndicAnalyzer()
