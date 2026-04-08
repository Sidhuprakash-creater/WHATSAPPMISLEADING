import asyncio
import time
import requests

BASE_URL = "http://localhost:8000/api/v1/analyze"

def test_scan(text, label):
    print(f"\n🧪 Testing {label}: '{text[:50]}...'")
    start = time.time()
    try:
        response = requests.post(BASE_URL, json={"text": text, "content_type": "text"}, timeout=30)
        duration = time.time() - start
        if response.status_code == 200:
            res = response.json()
            print(f"✅ Result: {res.get('verdict')} (Score: {res.get('risk_score')})")
            print(f"⏱️ Time Taken: {duration:.2f} seconds")
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    # 1. Fake/Rumor News
    test_scan("Breaking: Famous MLA Abhimanyu sethi died in tragic car accident today in Bhubaneswar. Rumor viral on WhatsApp.", "FAKE NEWS/RUMOR")
    
    # 2. Real/Normal News
    test_scan("Odisha Chief Minister announces new digital literacy program for rural students starting next month.", "REAL/NORMAL NEWS")
