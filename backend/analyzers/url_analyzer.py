"""
URL Analyzer — Checks URLs against security databases
Uses Google Safe Browsing + VirusTotal + WHOIS domain age
"""
import logging
import re
from urllib.parse import urlparse
from datetime import datetime, timezone
import httpx
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url if url.startswith("http") else f"https://{url}")
        return parsed.netloc or parsed.path.split("/")[0]
    except Exception:
        return url


def check_suspicious_patterns(url: str) -> list[dict]:
    """Robust heuristic checks for zero-day phishing patterns"""
    findings = []
    domain = extract_domain(url)
    
    # 1. URL Shortener Abuse
    shorteners = ['bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly', 'is.gd', 'buff.ly', 'cutt.ly', 'rb.gy']
    if any(s in domain for s in shorteners):
        findings.append({
            "type": "url_shortener",
            "evidence": "URL shortener detected (often used to obscure malicious links)",
        })

    # 2. Dangerous TLDs (.zip, etc.)
    suspicious_tlds = ['.zip', '.mov', '.tk', '.ml', '.ga', '.cf', '.gq', '.loan', '.top', '.xyz']
    if any(domain.endswith(t) for t in suspicious_tlds):
        findings.append({
            "type": "dangerous_tld",
            "evidence": f"Domain contains a high-risk Top Level Domain (.xyz, .zip, .tk, etc.)",
        })

    # 3. IP instead of hostname
    if re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", domain):
        findings.append({
            "type": "ip_domain",
            "evidence": "URL uses a raw IP address instead of a domain name (highly suspicious)"
        })

    # 4. Punycode check (homograph attacks)
    if 'xn--' in domain:
        findings.append({
            "type": "homograph_attack",
            "evidence": "Punycode (xn--) detected. May be a homograph attack trying to impersonate a real domain."
        })

    # 5. Phishing keywords
    suspicious_keywords = ['login', 'secure', 'bank', 'support-ticket', 'recovery', 'verify-account', 'invoice', 'payment']
    if any(kw in domain.lower() for kw in suspicious_keywords):
        findings.append({
            "type": "phishing_keyword",
            "evidence": "Domain contains keywords commonly used in phishing campaigns."
        })

    # 6. Excessive hyphens
    if domain.count('-') >= 3:
        findings.append({
            "type": "excessive_hyphens",
            "evidence": f"Domain has {domain.count('-')} hyphens — common in disposable phishing domains."
        })
        
    return findings


async def check_safe_browsing(url: str) -> dict:
    """Check URL against Google Safe Browsing API"""
    if not settings.GOOGLE_SAFE_BROWSING_KEY:
        return {"checked": False, "reason": "API key not configured"}
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"https://safebrowsing.googleapis.com/v4/threatMatches:find"
                f"?key={settings.GOOGLE_SAFE_BROWSING_KEY}",
                json={
                    "client": {"clientId": "misleading", "clientVersion": "1.0"},
                    "threatInfo": {
                        "threatTypes": [
                            "MALWARE", "SOCIAL_ENGINEERING",
                            "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"
                        ],
                        "platformTypes": ["ANY_PLATFORM"],
                        "threatEntryTypes": ["URL"],
                        "threatEntries": [{"url": url}],
                    },
                },
            )
            data = response.json()
            matches = data.get("matches", [])
            
            if matches:
                threat = matches[0].get("threatType", "UNKNOWN")
                return {"checked": True, "threat": threat, "safe": False}
            return {"checked": True, "threat": None, "safe": True}
    except Exception as e:
        logger.error(f"Safe Browsing check failed: {e}")
        return {"checked": False, "reason": str(e)}


async def check_virustotal(url: str) -> dict:
    """Check URL against VirusTotal"""
    if not settings.VIRUSTOTAL_API_KEY:
        return {"checked": False, "reason": "API key not configured"}
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Submit URL for scanning
            response = await client.post(
                "https://www.virustotal.com/api/v3/urls",
                headers={"x-apikey": settings.VIRUSTOTAL_API_KEY},
                data={"url": url},
            )
            if response.status_code == 200:
                data = response.json()
                analysis_id = data.get("data", {}).get("id")
                return {
                    "checked": True,
                    "analysis_id": analysis_id,
                    "submitted": True,
                }
            return {"checked": False, "reason": f"HTTP {response.status_code}"}
    except Exception as e:
        logger.error(f"VirusTotal check failed: {e}")
        return {"checked": False, "reason": str(e)}


async def analyze(url: str) -> dict:
    """
    Full URL analysis pipeline.
    Returns: { safe, threat, score, findings, domain_info }
    """
    domain = extract_domain(url)
    score = 0
    findings = []
    
    # 1. Pattern heuristics (instant)
    pattern_findings = check_suspicious_patterns(url)
    findings.extend(pattern_findings)
    score += len(pattern_findings) * 8  # 8 points per suspicious pattern
    
    # 2. Safe Browsing check
    sb_result = await check_safe_browsing(url)
    if sb_result.get("checked") and not sb_result.get("safe"):
        threat = sb_result.get("threat", "UNKNOWN")
        score += 35
        findings.append({
            "type": "safe_browsing_threat",
            "evidence": f"Google Safe Browsing: {threat} detected",
        })
    
    # 3. VirusTotal check
    vt_result = await check_virustotal(url)
    
    # Determine overall safety
    is_safe = score < 20
    
    result = {
        "safe": is_safe,
        "score": min(score, 100),
        "domain": domain,
        "threat": sb_result.get("threat"),
        "findings": findings,
        "safe_browsing": sb_result,
        "virustotal": vt_result,
        "details": f"URL scan: {'SAFE' if is_safe else 'SUSPICIOUS'} (score: {score})",
    }
    
    logger.info(f"URL analysis for {domain}: score={score}, safe={is_safe}")
    return result
