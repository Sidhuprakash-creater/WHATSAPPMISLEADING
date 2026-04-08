import asyncio
import json
from ai_wrapper import llm_fallback

async def test_fallback():
    print("=== TESTING LLM FALLBACK RECONSTRUCTION ===")
    forensic_data = {
        "offline_score": 85,
        "offline_findings": ["Metadata match (Exif): Known AI generator detected."],
        "is_ai_heuristic": True,
        "ai_confidence_heuristic": 95.0,
        "mime_type": "image/jpeg"
    }
    
    try:
        result = await llm_fallback.reconstruct_image_analysis(forensic_data)
        print("\nReconstructed Analysis Result:")
        print(json.dumps(result, indent=2))
        
        if result.get("explanation"):
            print("\nSUCCESS: Fallback LLM provided reasoning.")
        else:
            print("\nFAILURE: Result is empty or malformed.")
            
    except Exception as e:
        print(f"\nCRITICAL ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_fallback())
