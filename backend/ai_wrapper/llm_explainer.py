"""
LLM Explainer — Deep reasoning via Groq API (Llama 3.3 70B)
Generates human-readable explanations for why content is risky
"""
import json
import logging
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SYSTEM_PROMPT = """You are a multilingual expert misinformation analyst (English, Hindi, Odia). 

REGIONAL CONTEXT & SAFETY RULES:
1. Odia Harmless Verbs: 'hei gala' (it happened), 'khai gala' (ate), 'soigala' (slept), 'jai gala' (went). If the text ONLY contains these, set intent to 'safe', is_public_figure: false, and llm_confidence_adjustment: -35.
2. Odia Risk Indicators: 'marigala' / 'marigale' (DIED), 'arrest' / 'jail' (ARRESTED). If a real person is mentioned with these, set severity: 'high' and is_public_figure: true.
3. Language: Handle Odia script, Hindi script, and transliterated Hinglish.

Analyze requirements:
1. Subject Gravity: ULTRA-SENSITIVE to rumors about politicians, leaders, or sensitive death news.
2. Primary Claim: English search query (5-8 words). 
3. Emotional manipulation: Check for fake shock/grief.

Return ONLY valid JSON.
{
  "patterns_found": [{"type": string, "evidence": string}],
  "severity": "low" | "medium" | "high" | "extreme",
  "primary_claim": string,
  "is_public_figure": boolean,
  "llm_confidence_adjustment": integer,
  "explanation": string
}"""


async def explain(text: str, ml_result: dict) -> dict:
    """
    Send content + ML result to Groq (Llama 3.3 70B) for deep reasoning.
    Returns structured analysis with patterns and explanation.
    """
    if not settings.GROQ_API_KEY:
        logger.warning("Groq API key not configured — skipping LLM analysis")
        return {
            "patterns_found": [],
            "llm_confidence_adjustment": 0,
            "explanation": "LLM analysis unavailable (API key not configured)",
        }
    
    try:
        from groq import Groq
        
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        label = ml_result.get("label", "unknown").upper()
        prob = ml_result.get("prob", 0)
        
        user_msg = f"""ML Verdict: {label} ({prob*100:.0f}% confidence)
Content: {text[:2000]}

Analyze this content for misinformation indicators and return JSON only."""
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=800,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        
        response_text = response.choices[0].message.content
        
        # Parse JSON response
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = {
                    "patterns_found": [],
                    "llm_confidence_adjustment": 0,
                    "explanation": response_text[:500],
                }
        
        # Validate structure
        if "patterns_found" not in result:
            result["patterns_found"] = []
        if "llm_confidence_adjustment" not in result:
            result["llm_confidence_adjustment"] = 0
        if "severity" not in result:
            result["severity"] = "low"
        if "primary_claim" not in result:
            result["primary_claim"] = ""
        if "is_public_figure" not in result:
            result["is_public_figure"] = False
        if "explanation" not in result:
            result["explanation"] = "Analysis completed."
        
        # Clamp adjustment to the new wider range
        result["llm_confidence_adjustment"] = max(-20, min(60, 
            result["llm_confidence_adjustment"]))
        
        logger.info(f"LLM analysis: {len(result['patterns_found'])} patterns found, "
                     f"adjustment: {result['llm_confidence_adjustment']}")
        
        return result
        
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        return {
            "patterns_found": [],
            "llm_confidence_adjustment": 0,
            "explanation": f"LLM analysis error: {str(e)}",
        }
