import os
import asyncio
import json
import logging
from typing import List
from dotenv import load_dotenv
from groq import AsyncGroq
from tqdm.asyncio import tqdm

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = AsyncGroq(api_key=GROQ_API_KEY)

LANGUAGES = {
    "english": "English (International/Indian)",
    "hindi": "Hindi (Devanagari script)",
    "odia": "Odia (Odia script)",
    "hinglish": "Hinglish (Hindi words written in Latin/English script, e.g., 'Kya haal hai')"
}

OUTPUT_FILE = "data/synthetic_dataset.jsonl"

async def generate_batch(lang_key: str, lang_desc: str, count: int = 50) -> List[str]:
    """Generate a batch of synthetic messages using Groq"""
    prompt = f"""
    Generate {count} unique, realistic short messages or news headlines in {lang_desc}.
    The messages should cover:
    1. Fake news / Rumors
    2. General chat
    3. Emergency alerts
    4. Casual conversation
    
    Format your response as a JSON list of strings only.
    No preamble, no explanation. Just the JSON list.
    Example: ["message 1", "message 2"]
    """
    
    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("messages", data.get("messages_list", list(data.values())[0]))
    except Exception as e:
        logger.error(f"Error generating {lang_key}: {e}")
        return []

async def main():
    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY not found in .env")
        return

    all_data = []
    
    print(f"🚀 Starting Knowledge Distillation (Dataset Generation)...")
    
    tasks = []
    for lang_key, lang_desc in LANGUAGES.items():
        # We do 2 batches of 50 for each to get 100 per language
        tasks.append(generate_batch(lang_key, lang_desc, 50))
        tasks.append(generate_batch(lang_key, lang_desc, 50))

    results = await tqdm.gather(*tasks, desc="Generating Languages")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for idx, messages in enumerate(results):
            lang_key = list(LANGUAGES.keys())[idx // 2]
            for msg in messages:
                entry = {"text": msg, "label": lang_key}
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                all_data.append(entry)

    print(f"✅ Dataset generated! Total samples: {len(all_data)}")
    print(f"📁 Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
