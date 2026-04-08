import json
import logging
import asyncio
from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

async def reconstruct_image_analysis(forensic_data: dict) -> dict:
    """
    Uses a Text-based LLM (Groq/Gemini-Pro) to reconstruct a professional image analysis
    based on forensic clues (Metadata, AI detection scores, binary matches).
    
    This is used as a fallback when the primary Vision model fails.
    """
    prompt = f"""You are a Digital Forensics Reasoning Engine.
Analyze the following forensic clues extracted from an image and provide a professional risk assessment.

FORENSIC CLUES:
{json.dumps(forensic_data, indent=2)}

TASK:
1. Reconstruct what the image might be based on metadata (Exif, Software tags).
2. Interpret the AI detection score (Offline ML) and binary signatures.
3. Provide a structured verdict.

Output ONLY a valid JSON object:
{{
  "ai_confidence": 0-100,
  "is_nsfw": true/false,
  "manipulation_signs": ["list any anomalies found"],
  "risk_level": "low/medium/high",
  "explanation": "Professional forensic summary of why this image is risky or safe based on the clues."
}}
"""

    # Try Groq first as it is very fast for reasoning
    if settings.GROQ_API_KEY:
        try:
            from groq import Groq
            client = Groq(api_key=settings.GROQ_API_KEY)
            
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Groq Fallback Failed: {e}")

    # Try Gemini Text-only as second fallback
    if settings.GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = await model.generate_content_async(prompt)
            # Basic JSON extraction
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1]
            return json.loads(text.strip())
        except Exception as e:
            logger.error(f"Gemini Text Fallback Failed: {e}")

    # Final hardcoded fallback if everything fails
    return {
        "ai_confidence": forensic_data.get("offline_score", 0),
        "is_nsfw": False,
        "manipulation_signs": forensic_data.get("offline_findings", []),
        "risk_level": "medium" if forensic_data.get("offline_score", 0) > 40 else "low",
        "explanation": "Automated forensic scan detected potential anomalies in file structure/metadata."
    }
