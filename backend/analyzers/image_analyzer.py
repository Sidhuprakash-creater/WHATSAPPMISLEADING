"""
Image Analyzer — Gemini 1.5 Flash Vision
Analyzes images for deepfakes, AI generation, and propaganda. Includes static offline fallback.
"""
import base64
import json
import logging
import httpx
import io
import asyncio
from PIL import Image, ExifTags
from config import get_settings
import google.generativeai as genai
from .cvt_adapter import get_cvt_scanner

try:
    import imagehash
except ImportError:
    imagehash = None

logger = logging.getLogger(__name__)
settings = get_settings()

AI_DETECTOR = None

# Ensure fallback reasoning is available
try:
    from ai_wrapper.llm_fallback import reconstruct_image_analysis
except ImportError:
    reconstruct_image_analysis = None

def get_ai_detector():
    """Lazy-load the AI-image-detector model only when needed."""
    global AI_DETECTOR
    if AI_DETECTOR is None:
        try:
            from transformers import pipeline
            logger.info("Initializing HuggingFace AI-Image-Detector model (First Use)...")
            AI_DETECTOR = pipeline("image-classification", model="umm-maybe/AI-image-detector")
        except Exception as e:
            logger.error(f"Failed to load AI-detector model: {e}")
            AI_DETECTOR = False  # Mark as failed to avoid retrying indefinitely
    return AI_DETECTOR if AI_DETECTOR is not False else None

# Sample Hashes for known misinformation images
KNOWN_FAKE_HASHES = [
    "ff81c3c3e1e1e3c3", # Random hypothetical hashes
    "c3c3e1c3ff81c3c3"
]
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY not configured. Falling back to Open Source offline heuristics.")

async def analyze(file_url: str) -> dict:
    """
    Multimodal Image Analysis using Gemini 1.5 Flash.
    """
    all_signs = []
    offline_findings = []
    offline_score = 0
    b64_image = None
    mime_type = "image/jpeg"

    # 1. Acquire Image Data
    if file_url.startswith("http"):
        try:
            async with httpx.AsyncClient() as hc:
                resp = await hc.get(file_url, timeout=10)
                if resp.status_code == 200:
                    b64_image = base64.b64encode(resp.content).decode("utf-8")
        except Exception as e:
            return _error_response("Failed to fetch remote image")
    elif file_url.startswith("data:"):
        try:
            prefix, b64_str = file_url.split(",", 1)
            b64_image = b64_str
            if "image/png" in prefix:
                mime_type = "image/png"
        except Exception:
            return _error_response("Invalid Base64 format")
    else:
        b64_image = file_url

    if not b64_image:
        return _error_response("Empty image payload")

    image_bytes = None
    try:
        image_bytes = base64.b64decode(b64_image)
    except Exception:
        return _error_response("Malformed base64")

    # 2. Open Source EXIF & Heuristic Analysis (Always run as baseline)
    offline_score = 0
    offline_findings = []
    decoded_string = image_bytes.decode('utf-8', errors='ignore')

    # Security check for payload manipulation
    if "<script>" in decoded_string.lower() or "javascript:" in decoded_string.lower() or "onload=" in decoded_string.lower():
        offline_score = 90
        all_signs.append("HIGH RISK: Code injection (XSS) detected inside image data.")
        return _build_response(offline_score, 0.0, False, all_signs, "high", "Code Injection intercepted.")

    # Open Source Python Pillow implementation for AI tagging
    is_ai = False
    ai_confidence = 0.0
    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
        
        # 1. perceptual hashing for known misinformation
        if imagehash:
            img_phash = str(imagehash.phash(pil_img))
            if img_phash in KNOWN_FAKE_HASHES:
                all_signs.append("Match found in local database: Known Misinformation.")
                offline_score = max(offline_score, 100)
                return _build_response(offline_score, 0.0, False, all_signs, "high", "Known Fake Image Detected via ImageHash.")

        exif = pil_img.getexif()
        has_camera_exif = False
        for k, v in list(exif.items()):
            tag_name = ExifTags.TAGS.get(k, str(k))
            val_str = str(v).lower()
            # If we see Make, Model, or Software from a real camera manufacturer, mark as "Real Camera"
            if tag_name in ['Make', 'Model', 'Software'] and any(brand in val_str for brand in ['apple', 'samsung', 'google', 'sony', 'nikon', 'canon', 'fuji']):
                has_camera_exif = True
                
            if any(ai_term in val_str for ai_term in ["midjourney", "dall-e", "stable diffusion", "ai generated", "comfyui"]):
                is_ai = True
                ai_confidence = 95.0
                all_signs.append(f"Metadata match ({tag_name}): Known AI generator detected.")
                offline_score = max(offline_score, 85)
                
        # ML Inference & Gemini Analysis (Parallelized)
        gemini_task = None
        if settings.GEMINI_API_KEY:
            try:
                system_prompt = '''You are a Senior Digital Forensics Expert specializing in AI-generation detection and misinformation.
Analyze the provided image with extreme scrutiny.

Output your findings ONLY as a valid JSON object with the exact following schema:
{
  "ai_confidence": 0-100,
  "is_nsfw": true/false,
  "manipulation_signs": ["list of specific forensic anomalies"],
  "extracted_text_claims": ["any text or propaganda identified"],
  "risk_level": "low/medium/high",
  "explanation": "Detailed forensic reasoning."
}

FORENSIC GUIDELINES FOR AI DETECTION:
1. CHECK ANATOMY: Look for extra/missing fingers, "melted" ears, hair that blends into the background, or asymmetrical eyes.
2. CHECK GEOMETRY: Look for warped straight lines in backgrounds (door frames, signs) which indicate diffusion distortion.
3. CHECK TEXTURES: AI often creates "plastic" skin that is overly smooth, or "painterly" grass/water.
4. CHECK LIGHTING: Look for "Cinematic" lighting that doesn't have a logical source, or shadows that don't match the sun/lights.
5. CHECK TEXT: Most AI fails at background text. If a sign or shirt has "jumbled" letters, it is 95%+ AI.

CRITICAL SCORING RULES:
- If it is a normal photo from a phone, set ai_confidence to 0-5.
- If it is a screenshot or a meme, set ai_confidence to 0-10.
- If it has professional HDR/editing, set ai_confidence to 0-15.
- ONLY score ABOVE 80 if you see TWO or more of the forensic artifacts listed above.
- If you see "Melted Text" or "Impossible Hands," score 95-100 immediately.

NSFW: Set true ONLY for nudity, gore, or extreme violence.'''
                # Using Gemini 3 Flash (found in available models)
                model = genai.GenerativeModel('gemini-3-flash-preview')
                parts = [{"mime_type": mime_type, "data": image_bytes}, system_prompt]
                gemini_task = asyncio.create_task(model.generate_content_async(contents=parts))
            except Exception as e:
                logger.error(f"Failed to prepare Gemini Task: {e}")

        ml_task = None
        detector = get_ai_detector()
        if not is_ai and detector:
            def _run_ml():
                return detector(pil_img)
            ml_task = asyncio.create_task(asyncio.to_thread(_run_ml))

        # Execute tasks in parallel
        tasks = []
        if gemini_task: tasks.append(gemini_task)
        if ml_task: tasks.append(ml_task)
        
        # Add Custom Custom CvT-13 Scanner
        cvt_scanner = get_cvt_scanner()
        cvt_task = asyncio.create_task(cvt_scanner.predict(pil_img))
        tasks.append(cvt_task)
        
        gemini_res = None
        ml_res = None
        cvt_res = None
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            idx = 0
            if gemini_task:
                gemini_res = results[idx]
                idx += 1
            if ml_task:
                ml_res = results[idx]
                idx += 1
            cvt_res = results[idx]

        # Process ML Result
        if ml_res and not isinstance(ml_res, Exception):
            art_score = 0.0
            for pred in ml_res:
                if pred['label'] == 'artificial':
                    art_score = float(pred['score'])
            
            # Recalibrated Threshold: Only trigger if > 0.75 (high confidence)
            if art_score > 0.75:
                is_ai = True
                ai_confidence = art_score * 100
                offline_findings.append(f"ML Scan: High confidence AI footprint (Conf: {ai_confidence:.1f}%).")
                offline_score = max(offline_score, int(ai_confidence))
            elif art_score > 0.40:
                offline_findings.append(f"ML Scan: Suspected AI artifacts (Conf: {art_score*100:.1f}%).")
                ai_confidence = art_score * 100 # Keep for consolidation, but don't force 'is_ai' flag here
                offline_score = max(offline_score, 40)
            else:
                logger.debug(f"ML Scan: Image appears authentic (AI Score: {art_score:.2f})")
        elif isinstance(ml_res, Exception):
            logger.error(f"Local ML Inference failed: {ml_res}")

        # Process Custom CvT Result
        if cvt_res and not isinstance(cvt_res, Exception):
            cvt_label = cvt_res.get('label', 'real')
            cvt_conf = cvt_res.get('confidence', 0.0)
            
            if cvt_label == 'fake' and cvt_conf > 50:
                is_ai = True
                ai_confidence = max(ai_confidence, cvt_conf)
                offline_findings.append(f"Custom CvT-13 Scan: High-precision AI detection ({cvt_conf:.1f}% confidence).")
                offline_score = max(offline_score, int(cvt_conf))
            elif cvt_label == 'real' and cvt_conf > 90:
                offline_findings.append(f"Custom CvT-13 Scan: Authenticated as likely human-made ({cvt_conf:.1f}% confidence).")
        elif isinstance(cvt_res, Exception):
            logger.error(f"Custom CvT Scan failed: {cvt_res}")

    except Exception as e:
        logger.warning(f"Exif parse / ML setup failed: {e}")

    # Binary check fallback
    if not is_ai:
        if "midjourney" in decoded_string.lower() or "dall-e" in decoded_string.lower() or "ai_generated" in decoded_string.lower():
            is_ai = True
            ai_confidence = 85.0
            offline_findings.append("Image binary signature suggests it is AI-generated (Offline Scan).")
            offline_score = max(offline_score, 85)

    if not settings.GEMINI_API_KEY:
        if is_ai:
            return _build_response(offline_score, ai_confidence, False, offline_findings, "high", "Open Source AI Match")
        return _build_response(0, 0.0, False, all_signs, "low", "No offline anomalies detected.")

    # Process Gemini Result
    gemini_ai_conf = 0.0
    is_nsfw_detected = False
    gemini_signs = []
    gemini_explanation = "Vision Scan Completed"
    gemini_score = 20

    if gemini_res and not isinstance(gemini_res, Exception):
        # ... (parsing logic)
        try:
            # (Same parsing logic as before, just ensuring it's robust)
            text_resp = gemini_res.text
            if "```json" in text_resp:
                json_str = text_resp.split("```json")[1].split("```")[0].strip()
            elif "```" in text_resp:
                json_str = text_resp.split("```")[1].strip()
            else:
                json_str = text_resp.strip()
            
            result = json.loads(json_str)
            gemini_ai_conf = float(result.get("ai_confidence", 0.0))
            is_nsfw_detected = result.get("is_nsfw", False)
            gemini_signs = result.get("manipulation_signs", [])
            gemini_explanation = result.get("explanation", "Forensic Vision Scan Completed")
            
            risk_map = {"low": 10, "medium": 50, "high": 85}
            gemini_score = risk_map.get(str(result.get("risk_level", "low")).lower(), 20)
        except Exception as e:
            logger.error(f"Failed to parse Gemini JSON: {e}")
            gemini_explanation = f"Vision Parsing Error: {str(e)[:50]}"
            
    elif isinstance(gemini_res, Exception) or not gemini_res:
        logger.warning(f"Gemini 3 Flash failed (or 404): {gemini_res}. Trying Gemini 3 PRO Fallback...")
        try:
            # UPGRADE TO GEMINI 3 PRO for high-fidelity fallback
            pro_model = genai.GenerativeModel('gemini-3-pro-preview')
            pro_res = await pro_model.generate_content_async(contents=[{"mime_type": mime_type, "data": image_bytes}, system_prompt])
            
            text_resp = pro_res.text
            json_str = text_resp.split("```json")[1].split("```")[0].strip() if "```json" in text_resp else text_resp.strip()
            result = json.loads(json_str)
            
            gemini_ai_conf = float(result.get("ai_confidence", 0.0))
            is_nsfw_detected = result.get("is_nsfw", False)
            gemini_signs = result.get("manipulation_signs", [])
            gemini_explanation = result.get("explanation", "Next-Gen Pro Scan Completed")
            
            risk_map = {"low": 10, "medium": 50, "high": 85}
            gemini_score = risk_map.get(str(result.get("risk_level", "low")).lower(), 20)
        except Exception as pro_e:
            logger.error(f"Gemini Pro also failed: {pro_e}")
            # Final fallback to reconstruction
            if reconstruct_image_analysis:
                fallback_res = await reconstruct_image_analysis({"offline_findings": all_signs})
                gemini_ai_conf = float(fallback_res.get("ai_confidence", 0.0))
                gemini_signs = fallback_res.get("manipulation_signs", [])
                gemini_explanation = "Forensic Analysis Reconstructed (Vision Offline)"

    # ── CONSENSUS MERGE (Nuanced Decision Engine) ─────────────────────────
    # Combine Gemini (high-fidelity) with local ML (heuristic)
    # Gemini has a 70% weight, Local ML has 30% weight
    final_ai_conf = (gemini_ai_conf * 0.7) + (ai_confidence * 0.3)
    
    # ── EXIF Camera "Protection" Bonus ───────────────────────────────────
    # If genuine device labels exist (Apple/Samsung/Sony), apply a -50% penalty
    # to the AI score to prevent false positives on real photography noise.
    if has_camera_exif:
        logger.info("📸 Real camera hardware detected in EXIF — applying AI confidence penalty.")
        final_ai_conf = final_ai_conf * 0.5
        all_signs.append("Hardware Metadata: Authenticated as device-captured photography.")

    # Merge all findings
    all_signs.extend(gemini_signs)
    
    final_score = max(gemini_score, offline_score)
    
    # Force visibility: If AI confidence is very high, the risk score MUST be high
    if final_ai_conf > 75:
        final_score = max(final_score, int(final_ai_conf))
        
    final_risk_level = "high" if final_score >= 75 else ("medium" if final_score >= 35 else "low")
    final_context = gemini_explanation
    if all_signs:
        final_context = " | ".join(all_signs[:3]) + " | " + final_context
        
    return _build_response(
        score=final_score,
        ai_score=final_ai_conf,
        is_nsfw=is_nsfw_detected,
        manipulation_signs=all_signs,
        risk_level=final_risk_level,
        context=final_context
    )


def _build_response(score, ai_score, is_nsfw, manipulation_signs, risk_level, context):
    safe = score < 50
    return {
        "analyzed": True,
        "score": int(score),
        "ai_generated": float(ai_score),
        "nsfw": bool(is_nsfw),
        "analysis": {
            "manipulation_signs": manipulation_signs,
            "claims_made": [],
            "emotional_triggers": [],
            "risk_level": risk_level,
            "context_assessment": context,
            "safe_to_forward": safe and not is_nsfw
        },
        "details": f"Vision Scan: {risk_level.title()} risk"
    }


def _error_response(reason: str) -> dict:
    return {
        "analyzed": False,
        "reason": reason,
        "score": 0,
        "nsfw": False,
        "ai_generated": 0.0,
        "analysis": {
            "manipulation_signs": [reason],
            "risk_level": "low",
            "context_assessment": reason,
            "safe_to_forward": True,
            "claims_made": [],
            "emotional_triggers": []
        },
        "details": f"Error: {reason}"
    }
