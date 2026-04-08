"""
Entity Enricher — Enriches named entities with background context.
Priority 1: Pre-built local cache (instant, 0ms)
Priority 2: Wikipedia API fallback (async, ~1-2s, only if not in cache)
"""
import json
import logging
import os
import asyncio

logger = logging.getLogger(__name__)

# ── Load local pre-built politicians/business DB ─────────────────────────
_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "politicians_db.json")
_LOCAL_DB: dict = {}

try:
    with open(_DB_PATH, "r", encoding="utf-8") as f:
        _LOCAL_DB = json.load(f)
    logger.info(f"✅ Entity DB loaded: {len(_LOCAL_DB)} known entities")
except Exception as e:
    logger.warning(f"⚠️ Could not load politicians_db.json: {e}")


def _lookup_local(name: str) -> dict | None:
    """Case-insensitive lookup in local DB."""
    key = name.lower().strip()
    return _LOCAL_DB.get(key)

def contains_local_entity(text: str) -> bool:
    """Check if any key from the local entity DB appears in the text."""
    text_lower = text.lower()
    for key in _LOCAL_DB.keys():
        if key in text_lower:
            return True
    return False


async def _fetch_wikipedia(name: str) -> dict | None:
    """
    Fetches a 2-sentence Wikipedia summary for the given name.
    Has a strict 3-second timeout to never block the pipeline.
    """
    try:
        import httpx
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + name.replace(" ", "_")
        
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                extract = data.get("extract", "")
                # Take first 2 sentences max
                sentences = extract.split(". ")
                summary = ". ".join(sentences[:2]).strip()
                if summary and len(summary) > 20:
                    return {
                        "name": data.get("title", name),
                        "wikipedia_summary": summary,
                        "type": "public_figure",
                        "source": "wikipedia"
                    }
    except Exception as e:
        logger.debug(f"Wikipedia fetch failed for '{name}': {e}")
    return None


async def enrich_entities(raw_entities: list[dict]) -> list[dict]:
    """
    Takes a list of entities from LLM output and enriches each one.
    Fetches all non-cached entities concurrently.
    """
    if not raw_entities:
        return []

    # Prepare tasks
    tasks = []
    
    async def process_single(entity):
        name = entity.get("name", "")
        if not name or len(name) < 2:
            return entity

        # Phase 1: Local cache hit
        local = _lookup_local(name)
        if local:
            merged = {**entity, **local}
            merged["source"] = "local_db"
            return merged

        # Phase 2: Wikipedia (Async)
        wiki_data = await _fetch_wikipedia(name)
        if wiki_data:
            merged = {**entity, **wiki_data}
            merged["source"] = "wikipedia"
            return merged
        
        # Phase 3: No enrichment found
        entity["source"] = "llm_only"
        return entity

    # Run all entity enrichments in parallel
    enriched = await asyncio.gather(*(process_single(e) for e in raw_entities), return_exceptions=True)
    
    # Filter out exceptions and return valid results
    return [e for e in enriched if isinstance(e, dict)]
