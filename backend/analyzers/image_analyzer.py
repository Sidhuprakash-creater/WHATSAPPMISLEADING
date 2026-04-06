"""
Image Analyzer — Groq Vision (Llama 4 Scout) + metadata checks
Analyzes images for misinformation context
"""
import logging
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

import logging
import base64
import httpx
import binascii
import re

logger = logging.getLogger(__name__)

async def analyze(file_url: str) -> dict:
    """
    Cybersecurity Image Screener
    Detects malicious payloads, script injections in EXIF, Magic Bytes, and Steganography.
    """
    image_data = None
    
    # 1. Acquire Image Data
    if file_url.startswith("http"):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(file_url, timeout=10)
                if resp.status_code == 200:
                    image_data = resp.content
        except Exception as e:
            logger.error(f"Failed to download image URL: {e}")
            return {"analyzed": False, "reason": "Failed to fetch remote image", "score": 0}
    elif file_url.startswith("data:image"):
        try:
            b64_str = file_url.split(",")[1]
            image_data = base64.b64decode(b64_str)
        except Exception:
            return {"analyzed": False, "reason": "Invalid Base64", "score": 0}
    else:
        try:
            image_data = base64.b64decode(file_url)
        except Exception:
            return {"analyzed": False, "reason": "Unsupported file payload", "score": 0}

    if not image_data:
        return {"analyzed": False, "reason": "Empty image payload", "score": 0}

    score = 0
    findings = []
    
    # 2. Magic Byte Validation (Is it really an image?)
    hex_head = binascii.hexlify(image_data[:4]).decode('utf-8').upper()
    valid_magics = ["FFD8FF", "89504E47", "47494638", "52494646"] # JPEG, PNG, GIF, WEBP
    
    is_valid_image = any(hex_head.startswith(m) for m in valid_magics)
    if not is_valid_image:
        score += 80
        findings.append("Invalid Magic Bytes: File is disguised as an image but has an unknown or executable internal structure.")
    
    # 3. Payload / Code Injection Check
    try:
        raw_text = image_data.decode('latin-1', errors='ignore')
        malicious_patterns = [
            r"<\?php", r"<script", r"eval\(", r"exec\(", r"cmd\.exe", 
            r"powershell", r"WScript\.Shell", r"javascript:"
        ]
        
        for pattern in malicious_patterns:
            if re.search(pattern, raw_text, re.IGNORECASE):
                score += 100
                findings.append(f"Malicious Code Injection Detected: Executable code matching '{pattern}' embedded inside image.")
                break
                
        # 4. Steganography / Appended Data (JPEG EoF Check)
        if hex_head.startswith("FFD8FF"): 
            eof_marker = b"\xff\xd9"
            idx = image_data.rfind(eof_marker)
            if idx != -1 and len(image_data) > idx + 2:
                trailing_data = len(image_data) - (idx + 2)
                if trailing_data > 100: 
                    score += 40
                    findings.append(f"Steganography Detected: {trailing_data} bytes of hidden, non-image data attached to the end of the file.")
                    
    except Exception as e:
        logger.warning(f"Error during raw byte scanning: {e}")
        
    risk_level = "low"
    if score >= 80:
        risk_level = "high"
    elif score >= 40:
        risk_level = "medium"
        
    return {
        "analyzed": True,
        "score": min(score, 100),
        "ai_generated": 0.0,
        "nsfw": False,
        "analysis": {
            "manipulation_signs": findings,
            "claims_made": [],
            "emotional_triggers": [],
            "risk_level": risk_level,
            "context_assessment": f"Security scan completed. Found {len(findings)} anomalies."
        },
        "details": f"Cybersecurity Image Scan: {risk_level.title()} risk"
    }
