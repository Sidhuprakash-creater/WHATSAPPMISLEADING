"""
URL Analyzer — Google Safe Browsing + VirusTotal + Heuristics
Now returns FULL verdicts (not just submission IDs).
"""
import asyncio
import base64
import logging
import re
from urllib.parse import urlparse

import httpx

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def extract_domain(url: str) -> str:
    try:
        parsed = urlparse(url if url.startswith("http") else f"https://{url}")
        return parsed.netloc or parsed.path.split("/")[0]
    except Exception:
        return url


def check_suspicious_patterns(url: str) -> list[dict]:
    """Heuristic checks — instant, no API needed."""
    findings = []
    domain = extract_domain(url)

    shorteners = [
        "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly",
        "is.gd", "buff.ly", "cutt.ly", "rb.gy", "short.ly"
    ]
    if any(s in domain for s in shorteners):
        findings.append({
            "type": "url_shortener",
            "evidence": f"URL shortener '{domain}' detected — destination URL is hidden",
        })

    suspicious_tlds = [".zip", ".mov", ".tk", ".ml", ".ga", ".cf", ".gq", ".loan", ".top", ".xyz", ".click"]
    if any(domain.endswith(t) for t in suspicious_tlds):
        findings.append({
            "type": "dangerous_tld",
            "evidence": f"High-risk TLD on '{domain}' — commonly used by phishing sites",
        })

    if re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", domain):
        findings.append({
            "type": "ip_domain",
            "evidence": "URL uses a raw IP address instead of a domain name — highly suspicious",
        })

    if "xn--" in domain:
        findings.append({
            "type": "homograph_attack",
            "evidence": f"Punycode detected in '{domain}' — may be impersonating a legitimate site",
        })

    scam_keywords = [
        "prize", "winner", "lottery", "cash", "reward", "kbc", "lucky",
        "free-gift", "claim", "whatsapp-money", "pm-yojana", "modi-scheme"
    ]
    if any(kw in url.lower() for kw in scam_keywords):
        findings.append({
            "type": "financial_scam",
            "evidence": f"Phishing keyword found in URL: matches known scam patterns",
        })

    return findings


async def check_safe_browsing(url: str) -> dict:
    """Google Safe Browsing v4 — real-time threat check."""
    if not settings.GOOGLE_SAFE_BROWSING_KEY:
        return {"checked": False, "reason": "Google Safe Browsing API key not configured"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"https://safebrowsing.googleapis.com/v4/threatMatches:find"
                f"?key={settings.GOOGLE_SAFE_BROWSING_KEY}",
                json={
                    "client": {"clientId": "misleading", "clientVersion": "2.0"},
                    "threatInfo": {
                        "threatTypes": [
                            "MALWARE",
                            "SOCIAL_ENGINEERING",
                            "UNWANTED_SOFTWARE",
                            "POTENTIALLY_HARMFUL_APPLICATION",
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
                threat = matches[0].get("threatType", "UNKNOWN_THREAT")
                platform = matches[0].get("platformType", "ANY_PLATFORM")
                return {
                    "checked": True,
                    "safe": False,
                    "threat": threat,
                    "platform": platform,
                    "verdict": f"DANGEROUS — Google flagged as {threat}",
                }
            return {
                "checked": True,
                "safe": True,
                "threat": None,
                "verdict": "SAFE — Not in Google Safe Browsing threat database",
            }
    except Exception as e:
        logger.error(f"Google Safe Browsing check failed: {e}")
        return {"checked": False, "reason": str(e), "verdict": "Could not check"}


async def check_virustotal(url: str) -> dict:
    """
    VirusTotal URL check — submits AND fetches the full analysis result.
    Returns actual malicious engine count and full verdict.
    """
    if not settings.VIRUSTOTAL_API_KEY:
        return {"checked": False, "reason": "VirusTotal API key not configured"}

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            # Step 1: Submit URL (VirusTotal requires base64url encoded URL as ID)
            url_id = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")

            # Step 2: Try to GET analysis directly (avoids rate limits on re-scan)
            get_resp = await client.get(
                f"https://www.virustotal.com/api/v3/urls/{url_id}",
                headers={"x-apikey": settings.VIRUSTOTAL_API_KEY},
            )

            if get_resp.status_code == 200:
                data = get_resp.json()
                stats = (
                    data.get("data", {})
                    .get("attributes", {})
                    .get("last_analysis_stats", {})
                )
                malicious = stats.get("malicious", 0)
                suspicious = stats.get("suspicious", 0)
                harmless = stats.get("harmless", 0)
                total = malicious + suspicious + harmless + stats.get("undetected", 0)

                verdict = "SAFE"
                if malicious >= 3:
                    verdict = f"DANGEROUS — {malicious}/{total} engines flagged as MALICIOUS"
                elif malicious >= 1 or suspicious >= 2:
                    verdict = f"SUSPICIOUS — {malicious} malicious, {suspicious} suspicious detections"

                return {
                    "checked": True,
                    "malicious": malicious,
                    "suspicious": suspicious,
                    "harmless": harmless,
                    "total_engines": total,
                    "verdict": verdict,
                }
            elif get_resp.status_code == 404:
                # URL not in VT cache — submit for scan
                post_resp = await client.post(
                    "https://www.virustotal.com/api/v3/urls",
                    headers={"x-apikey": settings.VIRUSTOTAL_API_KEY},
                    data={"url": url},
                )
                if post_resp.status_code == 200:
                    return {
                        "checked": True,
                        "verdict": "Submitted for scan — not yet in VirusTotal database",
                        "malicious": 0,
                        "suspicious": 0,
                    }

            return {"checked": False, "reason": f"VirusTotal returned HTTP {get_resp.status_code}"}

    except Exception as e:
        logger.error(f"VirusTotal check failed: {e}")
        return {"checked": False, "reason": str(e)}


async def analyze(url: str) -> dict:
    """
    Full URL security pipeline.
    Runs Google Safe Browsing + VirusTotal in parallel, combines with heuristics.
    Returns rich structured result for Groq to reference.
    """
    domain = extract_domain(url)
    logger.info(f"Starting URL security scan for: {domain}")

    # Heuristics (instant)
    pattern_findings = check_suspicious_patterns(url)

    # GSB + VT in parallel
    gsb_result, vt_result = await asyncio.gather(
        check_safe_browsing(url),
        check_virustotal(url),
        return_exceptions=True,
    )

    if isinstance(gsb_result, Exception):
        gsb_result = {"checked": False, "reason": str(gsb_result)}
    if isinstance(vt_result, Exception):
        vt_result = {"checked": False, "reason": str(vt_result)}

    # Calculate score
    score = len(pattern_findings) * 8
    if gsb_result.get("checked") and not gsb_result.get("safe"):
        score += 50  # Hard penalty for confirmed threat
    vt_malicious = vt_result.get("malicious", 0) if isinstance(vt_result, dict) else 0
    if vt_malicious >= 3:
        score += 40
    elif vt_malicious >= 1:
        score += 15

    is_safe = score < 20

    result = {
        "url": url,
        "domain": domain,
        "safe": is_safe,
        "score": min(score, 100),
        "heuristic_findings": pattern_findings,
        "google_safe_browsing": gsb_result,
        "virustotal": vt_result,
        "threat": gsb_result.get("threat") if isinstance(gsb_result, dict) else None,
        "findings": pattern_findings,  # Keep for backwards compat with scoring.py
        "summary": (
            f"URL '{domain}': GSB={gsb_result.get('verdict', 'unchecked')}, "
            f"VT={vt_result.get('verdict', 'unchecked')}, "
            f"Heuristics={len(pattern_findings)} findings"
        ),
    }

    logger.info(f"URL scan complete for {domain}: score={score}, safe={is_safe}")
    return result
