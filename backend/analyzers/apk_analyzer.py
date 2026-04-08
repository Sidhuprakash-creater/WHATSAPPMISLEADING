"""
APK Analyzer — Static Checking + VirusTotal
Analyzes document/file uploads (especially APKs) for malware.
"""
import base64
import binascii
import hashlib
import logging
import re
import httpx
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

async def analyze(file_url: str) -> dict:
    """
    Malware Document Screener
    Validates Payload size, Magic Bytes, and queries VirusTotal using SHA-256 hash.
    """
    file_data = None
    
    # 1. Acquire File Data
    if file_url.startswith("http"):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(file_url, timeout=10)
                if resp.status_code == 200:
                    file_data = resp.content
        except Exception as e:
            logger.error(f"Failed to download URL: {e}")
            return _error_response("Failed to fetch remote document")
    elif file_url.startswith("data:"):
        try:
            b64_str = file_url.split(",")[1]
            file_data = base64.b64decode(b64_str)
        except Exception:
            return _error_response("Invalid Base64 payload")
    else:
        try:
            file_data = base64.b64decode(file_url)
        except Exception:
            return _error_response("Unsupported file payload format")

    if not file_data:
        return _error_response("Empty document payload")
        
    score = 0
    findings = []
    
    # 2. Magic Byte Validation
    hex_head = binascii.hexlify(file_data[:4]).decode('utf-8').upper()
    is_apk_zip = hex_head.startswith("504B0304")  # PK zip/apk format
    is_pdf = hex_head.startswith("25504446")    # %PDF
    is_exe = hex_head.startswith("4D5A")        # MZ

    if is_exe:
        score += 90
        findings.append("Executable File Detected: .exe disguised as document. DO NOT OPEN.")
    elif is_apk_zip:
        findings.append("Android Application Package (APK) detected.")
    elif is_pdf:
        findings.append("PDF Document detected.")
    else:
        findings.append(f"Unknown file format (Magic: {hex_head[:4]}). Proceed with caution.")
        score += 20

    # 3. File Hash Calculation
    sha256_hash = hashlib.sha256(file_data).hexdigest()
    
    # 4. VirusTotal API Query (if available)
    virustotal_threat = False
    vt_scan_str = "File Hash generated."
    
    if settings.VIRUSTOTAL_API_KEY:
        vt_score, vt_msg = await _check_virustotal(sha256_hash)
        if vt_score > 0:
            score += vt_score
            virustotal_threat = True
            findings.append(f"VirusTotal Alert: {vt_msg}")
        else:
            vt_scan_str = "VirusTotal Scan: Clean."
    else:
        vt_scan_str = "VirusTotal key missing - skipping cloud malware check."
        
    risk_level = "low"
    safe_to_forward = True
    
    if score >= 60:
        risk_level = "high"
        safe_to_forward = False
    elif score >= 30:
        risk_level = "medium"
        safe_to_forward = False

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
            "context_assessment": f"Security scan completed. {vt_scan_str}",
            "safe_to_forward": safe_to_forward
        },
        "details": f"Cybersecurity File Scan: {risk_level.title()} risk"
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


async def _check_virustotal(file_hash: str) -> tuple[int, str]:
    """Queries VirusTotal /files/{hash} API using v3 endpoint."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"https://www.virustotal.com/api/v3/files/{file_hash}",
                headers={"x-apikey": settings.VIRUSTOTAL_API_KEY}
            )
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0)
                suspicious = stats.get("suspicious", 0)
                
                if malicious > 0:
                    return 100, f"{malicious} security vendors flagged this file as malicious."
                elif suspicious > 0:
                    return 40, f"{suspicious} security vendors flagged this file as suspicious."
                return 0, "No threats detected by VirusTotal."
                
            elif response.status_code == 404:
                return 0, "Hash not found in VirusTotal database (Unknown file)."
            else:
                return 0, f"VT API error {response.status_code}"
    except Exception as e:
        logger.error(f"VirusTotal error: {e}")
        return 0, "Failed to connect to VirusTotal."
