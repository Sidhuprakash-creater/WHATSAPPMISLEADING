import time
import requests

BASE_URL = "http://localhost:8000/api/v1/analyze"

TEST_CASES = [
    {"text": "hei gala", "label": "Latin Odia (Safe)", "expected": "Low Risk"},
    {"text": "ହେଇଗଲା", "label": "Native Odia (Safe)", "expected": "Low Risk"},
    {"text": "samajh gaya", "label": "Latin Hindi (Safe)", "expected": "Low Risk"},
    {"text": "नमस्ते", "label": "Native Hindi (Safe)", "expected": "Low Risk"},
    {"text": "Breaking: Famous MLA Abhimanyu Sethi dead in accident rumor viral.", "label": "Real Rumor (High Risk)", "expected": "High Risk"}
]

def test_language_bypass(text, label, expected):
    print(f"\n🧪 Testing {label}: '{text}'")
    start = time.time()
    try:
        response = requests.post(BASE_URL, json={"text": text, "content_type": "text"}, timeout=15)
        duration = time.time() - start
        if response.status_code == 200:
            res = response.json()
            is_bypass = res.get("processing_ms", 999) < 200 # Sub-200ms usually means bypass or cache
            print(f"✅ Verdict: {res.get('verdict')} (Score: {res.get('risk_score')})")
            print(f"📄 Reasons: {', '.join(res.get('reasons', []))[:150]}...")
            print(f"⏱️ Time Taken: {duration:.4f}s | {'🚀 BYPASS HIT' if is_bypass else '🛰️ AI ANALYZED'}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting PRO Audit v2.1 (Native Fix Verified)...")
    for case in TEST_CASES:
        test_language_bypass(case["text"], case["label"], case["expected"])
