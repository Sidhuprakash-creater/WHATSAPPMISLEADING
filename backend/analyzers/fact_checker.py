"""
Semantic Fact-Checker Engine
Uses sentence-transformers & FAISS to search claims against a curated database of known truths & scams.
"""
import logging
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
        """Loads model and indexes the fact database. Run this on app startup."""
        if self._initialized:
            return
            
        try:
            from sentence_transformers import SentenceTransformer
            import faiss
            import numpy as np
            
            logger.info("Initializing Fact-Check Engine: Loading Sentence Transformer...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Prepare vectors
            self.texts = [item["text"] for item in FACT_DATABASE]
            logger.info(f"Encoding {len(self.texts)} facts for FAISS index...")
            embeddings = self.model.encode(self.texts, convert_to_numpy=True)
            
            # Initialize FAISS L2 distance index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings)
            
            self._initialized = True
            logger.info("Fact-Check Engine Online.")
        except ImportError as e:
            logger.warning(f"Fact-Check Engine dependencies missing (faiss/sentence-transformers): {e}")
        except Exception as e:
            logger.error(f"Failed to initialize Fact-Check Engine: {e}")

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
        Filters out mythological clutter (e.g. Mahabharata) to ensure political hoaxes are caught.
        """
        from .web_search_engine import search_engine
        
        results = []
        for claim in claims:
            search_results = await search_engine.search_claim(claim)
            
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
                # If we found results but they were ALL mythological/irrelevant for a real-life claim
                status = "not_found" # Force re-evaluation by scoring override
                
            results.append({
                "claim": claim,
                "status": status,
                "evidence": evidence,
                "source": "web_search"
            })
            
        return results

# Singleton instance
engine = FactCheckEngine()
