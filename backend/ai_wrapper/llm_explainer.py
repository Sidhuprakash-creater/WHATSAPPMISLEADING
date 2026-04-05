"""
LLM Explainer — Deep reasoning via Claude API
Generates human-readable explanations for why content is risky
"""
import json
import logging
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SYSTEM_PROMPT = """You are an expert misinformation detection analyst.
When given content and a preliminary ML verdict, analyze for:
1. Emotional manipulation (fear, urgency, outrage, guilt)
2. Missing or unverifiable sources
3. Viral forwarding language ('share before deleted', 'forward to all')
4. Factual inconsistencies or impossible claims
5. Conspiracy framing or anti-establishment rhetoric
6. Domain/author credibility signals

Return ONLY valid JSON. No markdown, no prose outside JSON.
Schema:
{
  "patterns_found": [{"type": string, "evidence": string}],
  "llm_confidence_adjustment": integer (-10 to +20),
  "explanation": string (2-3 sentences, human-readable)
}"""


async def explain(text: str, ml_result: dict) -> dict:
    """
    Send content + ML result to Claude for deep reasoning.
    Returns structured analysis with patterns and explanation.
    """
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("Anthropic API key not configured — skipping LLM analysis")
        return {
            "patterns_found": [],
            "llm_confidence_adjustment": 0,
            "explanation": "LLM analysis unavailable (API key not configured)",
        }
    
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        label = ml_result.get("label", "unknown").upper()
        prob = ml_result.get("prob", 0)
        
        user_msg = f"""ML Verdict: {label} ({prob*100:.0f}% confidence)
Content: {text[:2000]}

Analyze this content for misinformation indicators and return JSON only."""
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        
        response_text = response.content[0].text
        
        # Parse JSON response
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from response
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
        if "explanation" not in result:
            result["explanation"] = "Analysis completed."
        
        # Clamp adjustment
        result["llm_confidence_adjustment"] = max(-10, min(20, 
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
