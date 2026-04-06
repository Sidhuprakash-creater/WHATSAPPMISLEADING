import httpx
import asyncio
import json

BASE_URL = "http://127.0.0.1:8000/api/v1/language/detect-language"

TEST_CASES = [
    {"input": "Yeh free scheme hai", "expected": "Hinglish"},
    {"input": "This is fake news", "expected": "English"},
    {"input": "यह एक झूठी खबर है", "expected": "Hindi"},
    {"input": "ଏହା ଏକ ଭୁଲ ସନ୍ଦେଶ", "expected": "Odia"}
]

async def verify():
    print("🧪 Verifying Feature 1: Language Detection System...")
    
    async with httpx.AsyncClient() as client:
        for case in TEST_CASES:
            try:
                response = await client.post(BASE_URL, json={"text": case["input"]})
                if response.status_code == 200:
                    data = response.json()
                    status = "✅ PASS" if data["language"] == case["expected"] else "❌ FAIL"
                    print(f"{status} | Input: '{case['input']}' | Observed: {data['language']} | Confidence: {data['confidence']}")
                else:
                    print(f"❌ ERROR | Status: {response.status_code} | Body: {response.text}")
            except Exception as e:
                print(f"❌ CONNECTION ERROR | {e}")

if __name__ == "__main__":
    asyncio.run(verify())
