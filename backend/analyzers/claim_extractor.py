"""
Claim Extractor — Translates raw paragraph text into distinct verifiable factual claims.
Uses Groq API (fast LLM) to normalize language and extract claims clearly.
"""
import logging
import json
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

async def extract_claims(text: str) -> list[str]:
    """
    Extract core factual claims from a larger text block.
    Example: 
    Input: "OMG listen up guys! Govt giving 500 gb free data and laptops click here now http://xyz"
    Output: ["The Government is distributing free 500GB data", "The Government is distributing free laptops"]
    """
    if not text or len(text) < 10:
        return []
        
    if not settings.GROQ_API_KEY:
        logger.warning("Groq API Key missing. Skipping Claim Extraction.")
        return []
        
    try:
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        prompt = f"""
        Extract the core factual statements or claims made in the following text. 
        Format as a clean, standardized English sentence that can be fact-checked.
        Ignore emotional language, greetings, or URLs.
        
        Return ONLY valid JSON in this format:
        {{"claims": ["claim 1", "claim 2"]}}
        
        Text to analyze:
        "{text}"
        """
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        
        data = json.loads(response.choices[0].message.content)
        claims = data.get("claims", [])
        
        logger.info(f"Extracted {len(claims)} claims from text.")
        return claims
        
    except Exception as e:
        logger.error(f"Claim extraction failed: {e}")
        return []
