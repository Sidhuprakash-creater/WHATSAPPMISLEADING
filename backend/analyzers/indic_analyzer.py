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
        
        # ── PRIORITY 1: Instant Regional Safe-Verb Filter ─────────────────────
        # These are common Odia/Hinglish verbs that often trigger false positive scores 
        # because of the 'gala' suffix or similar character patterns.
        REGIONAL_SAFE_PATTERNS = [
            r"hei\s*gala", r"jai\s*gala", r"khai\s*gala", r"soi\s*gala", r"chaligala",
            r"ho\s*gaya", r"hai\s*gala", r"tha\s*gala", r"hobar", r"korichi",
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
