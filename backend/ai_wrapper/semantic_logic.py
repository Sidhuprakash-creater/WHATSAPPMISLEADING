import logging

logger = logging.getLogger(__name__)

class SemanticMemory:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        import faiss
        from sentence_transformers import SentenceTransformer
        import numpy as np
        logger.info(f"🧠 Initializing Semantic Memory (Heavy Load) with model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = 384  # Dimension for MiniLM-L6-v2
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []  # Stores the actual analysis results
        self.threshold = 0.85  # Similarity threshold
        self._np = np
        self._faiss = faiss

    def add_to_memory(self, text: str, result: dict):
        """Add a new scan result to semantic memory"""
        try:
            vector = self.model.encode([text])
            self.index.add(self._np.array(vector).astype('float32'))
            self.metadata.append(result)
            logger.info(f"✅ Added to Semantic Memory: {text[:30]}...")
        except Exception as e:
            logger.error(f"❌ Failed to add to semantic memory: {e}")

    def find_similar(self, text: str):
        """Search for similar past scans"""
        if self.index.ntotal == 0:
            return None
        
        try:
            vector = self.model.encode([text])
            # self.index.search returns D (distances) and I (indices)
            D, I = self.index.search(self._np.array(vector).astype('float32'), 1)
            
            # ULTRA-STRICT Threshold: 0.02 (Near-exact match only)
            distance = D[0][0]
            if distance < 0.02:
                logger.info(f"🎯 Semantic Match Found (High Confidence Distance: {distance:.4f})")
                return self.metadata[I[0][0]]
        except Exception as e:
            logger.error(f"❌ Semantic search failed: {e}")
        
        return None

_memory_instance = None

def get_memory():
    """Lazy-load semantic memory singleton on first request."""
    global _memory_instance
    if _memory_instance is None:
        try:
            # We don't log "Initializing" here to keep it quiet until actual heavy hit
            _memory_instance = SemanticMemory()
        except Exception as e:
            logger.error(f"❌ Failed to init semantic memory: {e}")
            return None
    return _memory_instance
