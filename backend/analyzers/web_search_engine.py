import logging
import asyncio
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

class WebSearchEngine:
    def __init__(self, max_results=5):
        self.max_results = max_results

    async def search_claim(self, query: str) -> list[dict]:
        """
        Searches the web with a strict timeout for production/hackathon performance.
        """
        try:
            # Strict 7-second timeout for web search
            loop = asyncio.get_event_loop()
            results = await asyncio.wait_for(
                loop.run_in_executor(None, self._sync_search, query),
                timeout=7.0
            )
            return results
        except asyncio.TimeoutError:
            logger.warning(f"Web search TIMED OUT for query '{query}' after 7s.")
            return []
        except Exception as e:
            logger.error(f"Web search failed for query '{query}': {e}")
            return []

    def _sync_search(self, query: str):
        with DDGS() as ddgs:
            # Robust extraction for multiple DDGS versions (6.x+)
            raw_results = ddgs.text(query)
            results = []
            for r in raw_results:
                if len(results) >= self.max_results:
                    break
                results.append({
                    "title": r.get("title"),
                    "body": r.get("body"),
                    "href": r.get("href")
                })
            return results

# Singleton instance
search_engine = WebSearchEngine()
