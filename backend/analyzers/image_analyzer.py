"""
Image Analyzer — Claude Vision + metadata checks
Analyzes images for misinformation context
"""
import logging
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def analyze(file_url: str) -> dict:
    """
    Analyze image for misinformation indicators.
    Uses Claude Vision API for deep analysis.
    """
    if not settings.ANTHROPIC_API_KEY:
        return {
            "analyzed": False,
            "reason": "Anthropic API key not configured",
            "score": 0,
        }
    
    try:
        import anthropic
        import httpx
        
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        # Download image and convert to base64
        async with httpx.AsyncClient(timeout=30) as http_client:
            response = await http_client.get(file_url)
            if response.status_code != 200:
                return {"analyzed": False, "reason": "Failed to download image", "score": 0}
            
            import base64
            image_data = base64.standard_b64encode(response.content).decode("utf-8")
            media_type = response.headers.get("content-type", "image/jpeg")
        
        # Analyze with Claude Vision
        vision_response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": """Analyze this image for misinformation indicators. Return ONLY valid JSON:
{
  "contains_text": true/false,
  "text_content": "any text visible in image",
  "claims_made": ["list of claims"],
  "manipulation_signs": ["any signs of editing/manipulation"],
  "emotional_triggers": ["fear/anger/urgency signals"],
  "ai_generated_probability": 0.0-1.0,
  "context_assessment": "brief assessment",
  "risk_level": "high/medium/low"
}""",
                    },
                ],
            }],
        )
        
        import json
        try:
            analysis = json.loads(vision_response.content[0].text)
        except json.JSONDecodeError:
            analysis = {"context_assessment": vision_response.content[0].text, "risk_level": "unknown"}
        
        # Calculate score
        score = 0
        if analysis.get("ai_generated_probability", 0) > 0.7:
            score += 20
        if analysis.get("risk_level") == "high":
            score += 25
        elif analysis.get("risk_level") == "medium":
            score += 15
        if analysis.get("emotional_triggers"):
            score += len(analysis["emotional_triggers"]) * 5
        
        return {
            "analyzed": True,
            "score": min(score, 100),
            "ai_generated": analysis.get("ai_generated_probability", 0),
            "nsfw": False,
            "analysis": analysis,
            "details": f"Image analysis: {analysis.get('risk_level', 'unknown')} risk",
        }
        
    except Exception as e:
        logger.error(f"Image analysis failed: {e}")
        return {
            "analyzed": False,
            "reason": str(e),
            "score": 0,
        }
