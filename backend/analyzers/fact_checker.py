"""
Semantic Fact-Checker Engine
Uses sentence-transformers & FAISS to search claims against a curated database of known truths & scams.
"""
import logging
import asyncio
import json

logger = logging.getLogger(__name__)

# Comprehensive Mock Fact Database for Regional Scams
FACT_DATABASE = [
    {
        "text": "The Government is not providing free laptops to students. Links claiming this are phishing scams.",
        "label": "TRUE_FACT",
        "tags": ["scam", "government", "laptops", "free"]
    },
    {
        "text": "Drinking hot water and inhaling steam does not cure COVID-19.",
        "label": "TRUE_FACT",
        "tags": ["medical", "health", "covid19"]
    },
    {
        "text": "The Prime Minister is not giving 500GB of free data for WhatsApp users.",
        "label": "TRUE_FACT",
        "tags": ["scam", "data", "telecom"]
    },
    {
        "text": "Reserve Bank of India (RBI) never sends emails asking for account details or passwords.",
        "label": "TRUE_FACT",
        "tags": ["scam", "rbi", "banking", "finance"]
    },
    {
        "text": "WhatsApp is not shutting down and you do not need to forward a message to 10 people to keep it active.",
        "label": "TRUE_FACT",
        "tags": ["whatsapp", "hoax", "chain letter"]
    },
    {
        "text": "Your electricity connection will NOT be disconnected at 9:30 PM tonight. SMS messages claiming this from random numbers are scams.",
        "label": "TRUE_FACT",
        "tags": ["scam", "electricity", "bill", "power"]
    },
    {
        "text": "TRAI (Telecom Regulatory Authority of India) does not block mobile numbers or call users demanding Aadhar verification.",
        "label": "TRUE_FACT",
        "tags": ["scam", "trai", "telecom", "aadhar", "police"]
    },
    {
        "text": "You have not won a 25 Lakh WhatsApp KBC lottery. Do not pay any processing fee or share bank details.",
        "label": "TRUE_FACT",
        "tags": ["scam", "lottery", "kbc", "whatsapp"]
    },
    {
        "text": "The government is not offering free solar panels or Rs 5000 directly to bank accounts under fake PM Yojana schemes via unauthorized WhatsApp links.",
        "label": "TRUE_FACT",
        "tags": ["scam", "yojana", "pm", "solar", "money"]
    },
    {
        "text": "Clicking links to 'upgrade your SIM to 5G' will not upgrade your phone but may compromise your banking app.",
        "label": "TRUE_FACT",
        "tags": ["scam", "5g", "sim", "telecom"]
    }
]

class FactCheckEngine:
    def __init__(self):
        self.model = None
        self.index = None
        self.texts = []
        self._initialized = False

    def initialize(self):
        """Spawns a background task to load models and index the fact database."""
        if self._initialized:
            return
            
        import asyncio
        asyncio.create_task(self._async_init())
        logger.info("Fact-Check Engine initialization started in BACKGROUND.")

    async def _async_init(self):
        """The actual heavy loading logic run in the background thread."""
        try:
            from sentence_transformers import SentenceTransformer
            import faiss
            import numpy as np
            
            logger.info("Fact-Check Background Task: Loading Sentence Transformer...")
            # Use to_thread for the CPU-bound loading
            self.model = await asyncio.to_thread(SentenceTransformer, 'all-MiniLM-L6-v2')
            
            # Prepare vectors
            self.texts = [item["text"] for item in FACT_DATABASE]
            logger.info(f"Fact-Check Background Task: Encoding {len(self.texts)} facts...")
            embeddings = await asyncio.to_thread(self.model.encode, self.texts, convert_to_numpy=True)
            
            # Initialize FAISS L2 distance index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings)
            
            self._initialized = True
            logger.info("✅ Fact-Check Engine is now ONLINE in background.")
        except ImportError as e:
            logger.warning(f"Fact-Check Engine background load failed (ImportError): {e}")
        except Exception as e:
            logger.error(f"Fact-Check Engine background load failed: {e}")

    async def check_claims(self, claims: list[str]) -> list[dict]:
        """
        Cross-references claims against the indexed database.
        Returns check results with distance metrics.
        """
        if not claims or not self._initialized:
            return []
            
        try:
            results = []
            import numpy as np
            
            # Encode incoming claims
            claim_embeddings = self.model.encode(claims, convert_to_numpy=True)
            
            # Search FAISS (k=1 nearest neighbor)
            distances, indices = self.index.search(claim_embeddings, k=1)
            
            for i, claim in enumerate(claims):
                dist = float(distances[i][0])
                match_idx = indices[i][0]
                matched_fact = FACT_DATABASE[match_idx]
                
                # Rule logic: 
                # L2 Distance generally under 1.0 means highly semantically related.
                # If related, our mocked db consists of DEBUNKING facts. 
                # e.g., claim: "govt gives free laptop" ~ fact: "govt does NOT give free laptops"
                # If they are semantically close, it's highly likely the claim is describing the debunked myth.
                
                status = "unverified"
                confidence = 0
                
                if dist < 1.2:  # Semantic threshold (adjust based on MiniLM-L6 geometry)
                    status = "debunked"
                    confidence = max(10, min(99, int((2.0 - dist) * 50)))
                
                results.append({
                    "claim": claim,
                    "matched_fact": matched_fact["text"] if dist < 1.5 else None,
                    "distance": dist,
                    "status": status,
                    "confidence": confidence
                })
                
            return results
        except Exception as e:
            logger.error(f"Fact-Checking failed: {e}")
            return []

    async def check_online_claims(self, claims: list[str]) -> list[dict]:
        """
        Searches the web for evidence regarding unknown or sensitive claims.
        Uses asyncio.gather to search multiple claims in parallel for extreme speed.
        """
        from .web_search_engine import search_engine
        import asyncio
        
        # Parallel Search: Query all claims at once with strict timeout
        search_tasks = [search_engine.search_claim(claim) for claim in claims]
        try:
            all_search_results = await asyncio.wait_for(
                asyncio.gather(*search_tasks),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            logger.warning(f"Parallel web search TIMED OUT after 15s for {len(claims)} claims.")
            all_search_results = [[] for _ in claims] # Return empty results for all if we hit total timeout
        
        results = []
        for i, claim in enumerate(claims):
            search_results = all_search_results[i]
            
            # Reality Filter: Filter out mythological noise
            filtered_results = []
            myth_keywords = ["mahabharata", "vyasa", "arjuna", "mythology", "ancient", "epic", "battle of kurukshetra"]
            
            for res in search_results:
                text_to_check = (res.get("title", "") + " " + res.get("body", "")).lower()
                if not any(k in text_to_check for k in myth_keywords):
                    filtered_results.append(res)

            status = "unverified"
            evidence = []
            
            if filtered_results:
                status = "found_online"
                evidence = filtered_results[:3]
            elif search_results:
                status = "not_found"
                
            results.append({
                "claim": claim,
                "status": status,
                "evidence": evidence,
                "source": "web_search"
            })
            
        return results

# Singleton instance
engine = FactCheckEngine()
