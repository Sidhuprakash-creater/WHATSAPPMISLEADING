import asyncio
import sys
import os
from dotenv import load_dotenv

# Add the backend directory to sys.path and load .env
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.append(backend_path)
load_dotenv(os.path.join(backend_path, ".env"))

from ai_wrapper.wrapper import run_full_analysis

async def test():
    print("--- Test 1ish: Political Threat (Fake News) ---")
    text1 = "Today Narendra Modi want to kill to Rahul Gandhi"
    result1 = await run_full_analysis({
        "content_type": "text",
        "text": text1,
        "ml_model": None
    })
    print(f"Text: {text1}")
    print(f"Verdict: {result1['verdict']}")
    print(f"Risk Score: {result1['risk_score']}")
    print(f"Reasons: {result1['reasons']}")
    
    print("\n--- Test 2: Natural Event (Non-Misinformation) ---")
    text2 = "An elephant killed a cat today in the village"
    result2 = await run_full_analysis({
        "content_type": "text",
        "text": text2,
        "ml_model": None
    })
    print(f"Text: {text2}")
    print(f"Verdict: {result2['verdict']}")
    print(f"Risk Score: {result2['risk_score']}")
    
    print("\n--- Test 3: Public Figure Rumor (Case Fix) ---")
    text3 = "Abhimanyu Sethi want to go dubai and here he can fix a deal with a drug mafia"
    result3 = await run_full_analysis({
        "content_type": "text",
        "text": text3,
        "ml_model": None
    })
    print(f"Text: {text3}")
    print(f"Verdict: {result3['verdict']}")
    print(f"Risk Score: {result3['risk_score']}")
    print(f"Reasons: {result3['reasons']}")

if __name__ == "__main__":
    asyncio.run(test())
