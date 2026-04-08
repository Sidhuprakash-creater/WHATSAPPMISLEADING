import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging to see absolute details
logging.basicConfig(level=logging.INFO)

async def test_performance():
    from ai_wrapper.wrapper import run_full_analysis
    
    test_data = {
        "text": "Breaking: Abhimanyu sethi mola rumor viral happening now",
        "content_type": "text",
        "ml_model": "llama-3.1-8b-instant"
    }
    
    print("\n🚀 Starting Diagnostic Scan...")
    try:
        result = await run_full_analysis(test_data)
        print("\n✅ SUCCESS!")
        print(f"Verdict: {result.get('verdict')}")
        print(f"Risk Score: {result.get('risk_score')}")
    except Exception as e:
        print("\n❌ CRASH DETECTED!")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_performance())
