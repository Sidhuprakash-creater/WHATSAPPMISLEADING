import asyncio
import logging
from ai_wrapper.wrapper import run_full_analysis

# Setup logging
logging.basicConfig(level=logging.INFO)

async def test_scenarios():
    test_cases = [
        {"text": "sab kichhi hei gala", "content_type": "text"}, # Safe (All happened)
        {"text": "abhimanyu sethi marigala", "content_type": "text"}, # Risk (Death)
    ]

    print("\n--- 🕵️ TESTING INDIC-BERT CONTEXT FIX ---\n")
    for case in test_cases:
        print(f"🔍 SCANNING: '{case['text']}'")
        result = await run_full_analysis(case)
        print(f"✅ VERDICT: {result['verdict']} (Score: {result['risk_score']})")
        print(f"📄 REASONS: {result['reasons']}")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(test_scenarios())
