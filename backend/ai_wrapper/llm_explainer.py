"""
LLM Explainer — Groq-Powered Misinformation Analysis Engine
Uses llama-3.3-70b-versatile for deep, content-specific analysis.
This is the PRIMARY and SOLE verdict source in the new pipeline.
The ML model is locked; Groq decides everything.
"""
import asyncio
import json
import logging

from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Best model for deep reasoning + speed
MODEL = "llama-3.3-70b-versatile"


# ── Language Detection ─────────────────────────────────────────────────────
def detect_language(text: str) -> str:
    """Fast rule-based language detector."""
    if not text:
        return "english"
    text_lower = text.lower()
    odia_chars = set("ଅଆଇଈଉଊଋଏଐଓଔକଖଗଘଙଚଛଜଝଞଟଠଡଢଣତଥଦଧନପଫବଭମଯରଲଳଵଶଷସହ")
    devanagari_chars = set("अआइईउऊऋएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह")
    if any(c in odia_chars for c in text):
        return "odia"
    if any(c in devanagari_chars for c in text):
        return "hindi"
    english_words = len([w for w in text_lower.split() if w.isascii()])
    total_words = len(text_lower.split())
    if total_words > 0 and english_words / total_words < 0.6:
        return "hinglish"
    return "english"


# ── Language Instructions ──────────────────────────────────────────────────
LANGUAGE_INSTRUCTIONS = {
    "odia": (
        "LANGUAGE INSTRUCTION: ତୁମର ସମ୍ପୂର୍ଣ JSON response ଓଡ଼ିଆ ଭାଷାରେ ଲେଖ। "
        "IMPORTANT: Output valid JSON format."
    ),
    "hindi": (
        "LANGUAGE INSTRUCTION: अपना पूरा JSON response हिंदी में लिखें। "
        "IMPORTANT: Output valid JSON format."
    ),
    "hinglish": (
        "LANGUAGE INSTRUCTION: Apna pura JSON response Hinglish mein likho "
        "(Hindi words + Roman script mix). IMPORTANT: Output valid JSON format."
    ),
    "english": (
        "LANGUAGE INSTRUCTION: Write your ENTIRE JSON response in English. "
        "IMPORTANT: Output valid JSON format. Do not use any other language script."
    ),
}


# ── Master System Prompt ────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are MisLEADING AI — India's most advanced real-time misinformation detection engine.

Your job: Analyze the given message with FORENSIC PRECISION and produce a structured JSON verdict.

CORE RULES:
1. EVERY field must be SPECIFIC to THIS message. Never use generic templates.
2. The "summary" must read like a journalist's report — name the specific claim, name specific entities, explain WHY it's problematic.
3. "why_fake" must list CONCRETE evidence-based reasons, not generic warnings.
4. "entities" must describe the ACTUAL people/orgs mentioned — include real background info.
5. "claim_vs_reality" must contrast EXACTLY what the message says vs. verified facts.
6. "patterns_found" must identify the SPECIFIC psychological trick used in THIS message.
7. URL FORENSICS (CRITICAL): If URL scan results are provided:
    - INTEGRATE those findings into your explanation.
    - Reference "Google Safe Browsing flagged this as SOCIAL_ENGINEERING (Phishing)" or "VirusTotal: [X] security engines detected MALWARE/MALICIOUS" directly.
    - If a link is detected as malicious, explain the TECHNICAL threat: "This link may attempt to steal your WhatsApp session tokens" or "This is a credential harvesting site designed to look like a bank login".
    - If the link is short (bit.ly, t.ly) and scan is clean, still advise caution about the hidden destination.
8. SEVERITY LOGIC:
    - "extreme": Death claims about public figures, viral medical hoaxes, imminent violence, or active Malware URL
    - "high": Financial scams with Phishing URLs, fake government schemes, impersonation
    - "medium": Unverified rumors, chain letters, misleading stats
    - "low": Normal conversation, safe content
9. STRICT INTENT ALIGNMENT: If the message is about DEATH/MURDER, your explanation must focus ONLY on morbidity/misinformation — never mention "scam" or "lottery". If it's about a PRIZE/SCAM, focus ONLY on financial fraud — never mention "death" unless present.
10. "safe_to_forward": true ONLY if score would be < 25 AND no threats detected (VT/GSB must be CLEAN).

OUTPUT FORMAT (strict JSON, no markdown, no extra text):
{
  "primary_claim": "The exact core assertion of this message in one sentence",
  "severity": "low|medium|high|extreme",
  "is_public_figure": true|false,
  "safe_to_forward": true|false,
  "llm_confidence_adjustment": 0,
  "why_fake": [
    "Specific reason 1 with evidence from the message",
    "Specific reason 2 with named entities or known facts",
    "Specific reason 3 referencing URL scan results (e.g. 'VirusTotal flagged this as Phishing')"
  ],
  "entities": [
    {
      "name": "Entity name",
      "type": "politician|celebrity|organization|government_body|other",
      "role": "Their actual real-world role",
      "party_or_company": "Party/org they belong to",
      "why_mentioned": "Why they appear in this message",
      "misuse_note": "How their identity/name is being exploited in this message",
      "background": "2-3 sentences of real factual background about this person/org"
    }
  ],
  "claim_vs_reality": [
    {
      "claim": "Exact claim from the message",
      "reality": "What is actually true according to verified sources",
      "source_hint": "PIB Fact Check / NDTV / WHO / cybercrime.gov.in / etc."
    }
  ],
  "patterns_found": [
    {
      "type": "Pattern name (Financial Bait / Urgency Pressure / Impersonation / Morbidity / Fear Mongering / Chain Letter / Fake Authority)",
      "evidence": "The exact phrase or element in the message that demonstrates this pattern"
    }
  ],
  "url_security_summary": "Deep forensic analysis of the URLs: Explain what GSB (Social Engineering/Malware) and VT (Vendor detections) found. If clean, explain why it's still suspicious if it's a scam link.",
  "summary": "A 3-5 sentence forensic report. Name the specific claim. Name specific entities. Explain the exact threat (misinformation or security threat like Phishing). Mention URL scan results explicitly. Use precise, professional language."
}"""


async def explain(
    text: str,
    url_scan_results: dict = None,
    fact_check_results: list = None,
    detected_lang: str = None
) -> dict:
    """
    Primary analysis function — Groq decides the FULL verdict.
    url_scan_results: combined output from Google Safe Browsing + VirusTotal
    detected_lang: pre-detected language code
    """
    if not settings.GROQ_API_KEY:
        return _fallback_result("GROQ_API_KEY not configured.")

    if not detected_lang:
        detected_lang = detect_language(text)

    lang_instruction = LANGUAGE_INSTRUCTIONS.get(
        detected_lang, LANGUAGE_INSTRUCTIONS["english"]
    )

    # Build URL context for the prompt
    url_context = ""
    if url_scan_results:
        url_context = f"\n\nURL SECURITY SCAN RESULTS (from live APIs):\n{json.dumps(url_scan_results, indent=2)}"

    # Build Fact Check context for the prompt
    fact_context = ""
    if fact_check_results:
        fact_context = f"\n\nFACT-CHECK EVIDENCE (Search results & Known truths):\n{json.dumps(fact_check_results, indent=2)}"

    user_msg = (
        f"{lang_instruction}\n\n"
        f"MESSAGE TO ANALYZE:\n{text[:2000]}"
        f"{url_context}"
        f"{fact_context}\n\n"
        f"Output JSON only. Be SPECIFIC to THIS message. No templates."
    )

    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=settings.GROQ_API_KEY)

        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=2500,
            temperature=0.05,
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)

        # Ensure all keys exist with safe defaults
        result.setdefault("primary_claim", "Unknown claim")
        result.setdefault("severity", "low")
        result.setdefault("is_public_figure", False)
        result.setdefault("safe_to_forward", True)
        result.setdefault("llm_confidence_adjustment", 0)
        result.setdefault("why_fake", [])
        result.setdefault("entities", [])
        result.setdefault("claim_vs_reality", [])
        result.setdefault("patterns_found", [])
        result.setdefault("url_security_summary", "")
        result.setdefault("summary", "")
        result["_detected_lang"] = detected_lang

        logger.info(
            f"Groq analysis complete | severity={result.get('severity')} | "
            f"lang={detected_lang} | safe={result.get('safe_to_forward')}"
        )
        return result

    except Exception as e:
        logger.error(f"Groq LLM failure: {e}")
        return _fallback_result(str(e))


def _fallback_result(reason: str) -> dict:
    return {
        "primary_claim": "Analysis unavailable",
        "severity": "low",
        "is_public_figure": False,
        "safe_to_forward": True,
        "llm_confidence_adjustment": 0,
        "why_fake": [f"Deep AI analysis could not complete: {reason[:100]}"],
        "entities": [],
        "claim_vs_reality": [],
        "patterns_found": [],
        "url_security_summary": "",
        "summary": "Deep analysis temporarily unavailable.",
        "_detected_lang": "english",
        "is_timeout": True,
    }
