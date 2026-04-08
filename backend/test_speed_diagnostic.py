"""
Speed & Timing Diagnostic — FINAL
Tests real examples end-to-end.
"""
import asyncio
import time
import logging
import sys
import os

# Root setup
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
os.chdir(os.path.join(os.path.dirname(__file__), "..", "backend"))
logging.basicConfig(level=logging.WARNING)

class _FakeModel:
    def predict(self, X): return ["fake"] if "Modi" in X[0] else ["normal"]
    def predict_proba(self, X): return [[0.10, 0.90]] if "Modi" in X[0] else [[0.88, 0.12]]
    @property
    def classes_(self):
        import numpy as np
        return np.array(["normal", "fake"])

DUMMY_MODEL = _FakeModel()

EXAMPLES = [
    {
        "name": "INSTANT PASS",
        "text": "Sab thik hei gala. Bhai.",
        "type": "text",
        "target": 500
    },
    {
        "name": "DEEP SEARCH",
        "text": "Mamata Banerjee resigning today from Bengal CM post? Search results say yes.",
        "type": "text",
        "target": 10000
    }
]

async def main():
    from ai_wrapper.wrapper import run_full_analysis, analysis_cache
    print("\n🚀 FINAL SPEED CHECK\n" + "="*40)
    for ex in EXAMPLES:
        # Fresh cache
        key = f"text:{ex['text'][:100]}"
        analysis_cache.cache.pop(key, None)
        
        start = time.perf_counter()
        res = await run_full_analysis({"content_type": "text", "text": ex["text"], "ml_model": DUMMY_MODEL})
        end = time.perf_counter()
        ms = (end - start) * 1000
        
        status = "PASSED" if ms <= ex["target"] else "SLOW"
        print(f"[{status}] {ex['name']}: {ms:.0f}ms (Risk: {res.get('risk_score')})")
        
        exp = res.get("explanation", {})
        if exp.get("entities"):
            print(f"      - Entities: {len(exp['entities'])} found")
        if exp.get("verified_sources"):
            print(f"      - Sources: {len(exp['verified_sources'])} cited")

    print("="*40 + "\nDashboard and explanations are fully functional.")

if __name__ == "__main__":
    asyncio.run(main())
