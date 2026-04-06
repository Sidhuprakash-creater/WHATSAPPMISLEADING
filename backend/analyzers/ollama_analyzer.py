import aiohttp
import json
import logging

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "misleading-ai"

logger = logging.getLogger(__name__)

async def analyze_with_ollama(text: str) -> dict:
    """
    Passes the input text to the highly trained Local Ollama language model.
    Expects a structured JSON response predicting scams, intent, and toxic language.
    """
    payload = {
        "model": MODEL_NAME,
        "prompt": text,
        "format": "json",    # Crucial: forces Ollama to return ONLY valid JSON
        "stream": False,
        "options": {
            "temperature": 0.2 # Lower temperature for less hallucination
        }
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(OLLAMA_URL, json=payload, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    response_text = data.get("response", "{}")
                    try:
                        # Parse the JSON strictly provided by Ollama
                        result_dict = json.loads(response_text)
                        
                        # Apply fallback logic if some expected keys are missing
                        return {
                            "detected_language": result_dict.get("detected_language", "Unknown"),
                            "content_category": result_dict.get("content_category", "Normal"),
                            "intent_to_harm": result_dict.get("intent_to_harm", False),
                            "severity_score": result_dict.get("severity_score", 0),
                            "explanation": result_dict.get("explanation", "Could not fully determine context.")
                        }
                    except json.JSONDecodeError:
                        logger.error("Ollama returned invalid JSON")
                        return generate_fallback(text)
                else:
                    logger.error(f"Ollama API error: {response.status}")
                    return generate_fallback(text)
    except Exception as e:
        logger.error(f"Failed to connect to local Ollama instance: {e}")
        return generate_fallback(text)

def generate_fallback(text: str) -> dict:
    """Fallback if Ollama is not running."""
    return {
        "detected_language": "Unknown (Ollama offline)",
        "content_category": "Normal",
        "intent_to_harm": False,
        "severity_score": 0,
        "explanation": "Local LLM analyzer is offline or failed."
    }

# Sync test function
if __name__ == "__main__":
    import asyncio
    test_text = "Jio users ke liye khushkhabri! Is link par click karein aur payein 3 mahine ka free recharge: http://free-jio-recharge.xyz"
    result = asyncio.run(analyze_with_ollama(test_text))
    print(json.dumps(result, indent=2))
