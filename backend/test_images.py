import asyncio
import json
import base64
from analyzers import image_analyzer

async def main():
    print("=== TEST 1: GEMINI API ANALYSIS (REAL IMAGE) ===")
    # Using a working image URL
    payload = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/25.png"
    
    result = await image_analyzer.analyze(payload)
    print("Normal Image Result (Gemini):")
    print(f"NSFW Flag: {result.get('nsfw')}")
    print(json.dumps(result, indent=2))

    print("\n=== TEST 2: OFFLINE MALICIOUS DETECTOR (INJECTED SCRIPT) ===")
    # Encode '<script>alert("Hacked")</script>' into base64 correctly
    malicious_data = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;"
    hacker_payload = malicious_data + b"<script>alert('Internal Code Injection')</script>"
    payload_hack = f"data:image/gif;base64,{base64.b64encode(hacker_payload).decode('utf-8')}"
    
    result2 = await image_analyzer.analyze(payload_hack)
    print("Injected Image Result (Offline + Gemini Logic):")
    print(json.dumps(result2, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
