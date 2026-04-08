import time
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_speed(text, scenario):
    print(f"\n🧪 Scanning {scenario}: '{text}'")
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/analyze", 
            json={"text": text, "content_type": "text"},
            timeout=20
        )
        duration = time.time() - start
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Result: {data.get('verdict')} (Score: {data.get('risk_score')})")
            print(f"⏱️ Time taken: {duration:.2f} seconds")
            return duration
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    return 999

if __name__ == "__main__":
    print("🚀 Starting PRO Speed Verification...")
    
    # 1. First Time (Should trigger Regex/ML)
    t1 = test_speed("Sab kichhi hei gala", "Odia Safe (Initial)")
    
    # 2. Second Time (Should be INSTANT Cache - 0ms)
    t1_cached = test_speed("Sab kichhi hei gala", "Odia Safe (Cached)")
    
    # 3. Deep Analysis (Should trigger Fast Parallel AI)
    t2 = test_speed("Abhimanyu sethi mla marigale", "Odia Risk Rumor")
    
    print("\n" + "="*30)
    print(f"🏆 Speed Stats:")
    print(f"- Regex/ML Path: {t1:.2f}s")
    print(f"- Cache Path: {t1_cached:.2f}s (BOOSTER! ✨)")
    print(f"- Parallel AI Path: {t2:.2f}s (TURBO! 🏎️)")
    print("="*30)
