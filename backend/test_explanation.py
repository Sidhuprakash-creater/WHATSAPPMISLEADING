import asyncio
import os
import sys

# Root setup
sys.path.insert(0, os.path.dirname(__file__))

from ai_wrapper.wrapper import run_full_analysis, analysis_cache

class _FakeModel:
    def predict(self, X): return ["fake"] if "Modi" in X[0] else ["normal"]
    def predict_proba(self, X): return [[0.10, 0.90]] if "Modi" in X[0] else [[0.88, 0.12]]
    @property
    def classes_(self):
        import numpy as np
        return np.array(["normal", "fake"])

DUMMY_MODEL = _FakeModel()

async def main():
    print("\n--- TEST FULL ANALYSIS ---")
    
    analysis_cache.cache.clear() # Clear cache to force run

    fake_text = "Modi has announced 50000 rupees to everyone's account! Send this message to 10 people to claim."
    print("Testing fake message:", fake_text)

    input_data = {
        "content_type": "text",
        "text": fake_text,
        "ml_model": DUMMY_MODEL
    }
    
    res = await run_full_analysis(input_data)
    
    import json
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
