"""
MisLEADING — FastAPI Application Factory
Main entry point for the backend API server
"""
import os
import asyncio
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


# ── Lifespan (startup/shutdown events) ──────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    ULTRA-LEAN Lifespan: Purpose is to reach 'yield' as fast as possible.
    All heavy lifting is deferred to background tasks.
    """
    logger.info("🚀 MisLEADING API: Instant Sequential Start Initiated...")
    
    # Placeholder state
    app.state.ml_model = None
    app.state.redis = None
    app.state.fact_engine = None

    async def background_init():
        logger.info("🕒 [Background] Starting deferred initializations...")
        
        # 1. Database
        try:
            from db.database import engine, Base
            import db.models
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ [Background] Database Tables ready.")
        except Exception as e:
            logger.error(f"❌ [Background] DB Init Failed: {e}")

        # 2. Fact-Check Engine
        try:
            from analyzers.fact_checker import FactCheckEngine
            app.state.fact_engine = FactCheckEngine()
            app.state.fact_engine.initialize()
            logger.info("✅ [Background] Fact-Check Engine initialized.")
        except Exception as e:
            logger.error(f"❌ [Background] Fact-Check Init Failed: {e}")

        # 3. ML Model
        model_path = os.path.join(os.path.dirname(__file__), "ml", "model.pkl")
        if os.path.exists(model_path):
            try:
                import joblib
                app.state.ml_model = await asyncio.to_thread(joblib.load, model_path)
                logger.info("✅ [Background] ML Model loaded.")
            except Exception as e:
                logger.error(f"❌ [Background] ML Model load fail: {e}")

        # 4. Redis
        try:
            import redis.asyncio as aioredis
            app.state.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await asyncio.wait_for(app.state.redis.ping(), timeout=3.0)
            logger.info("✅ [Background] Redis connected.")
        except Exception:
            app.state.redis = None
            logger.warning("⚠️ [Background] Redis unavailable (Cache bypassed).")

    # Launch everything in ONE background task to not block reaching yield
    init_task = asyncio.create_task(background_init())
    
    yield  # SERVER IS NOW LIVE AND LISTENING ON PORT 8000

    # Shutdown
    logger.info("🛑 MisLEADING API: Closing connections...")
    init_task.cancel() # Stop init if it's still running
    if app.state.redis:
        try: await app.state.redis.close()
        except: pass
    logger.info("🛑 MisLEADING API: Stopped.")


# ── Create FastAPI App ──────────────────────────────────────
app = FastAPI(
    title="MisLEADING API",
    description="Multi-Modal AI Misinformation Detection System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS Middleware ─────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health Check ────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "ml_model_loaded": app.state.ml_model is not None,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "redis": app.state.redis is not None,
        "ml_model": app.state.ml_model is not None,
    }

@app.post("/api/v1/clear_cache", tags=["Maintenance"])
async def clear_cache():
    """Manual cache purge for development/testing"""
    try:
        from ai_wrapper.wrapper import analysis_cache
        from ai_wrapper.semantic_logic import get_memory
        mem = get_memory()

        # 1. Clear In-memory state
        analysis_cache.cache = {}
        if mem:
            mem.metadata = []
            mem.index.reset()
        logger.info("Cache and semantic memory cleared.")

        # 2. Hard Physical Deletion
        cache_locations = [
            os.path.join("data", "analysis_cache.json"),
            os.path.join("backend", "data", "analysis_cache.json")
        ]
        
        for cache_path in cache_locations:
            if os.path.exists(cache_path):
                os.remove(cache_path)
                logger.info(f"🗑️ Deleted: {cache_path}")
        
        # Ensure we're in a clean state
        analysis_cache.cache = {}
        analysis_cache._save()

        logger.info("🧹 SYSTEM CACHE PURGED Physically and Mentally.")
        return {"status": "success", "message": "Persistent and Semantic caches physically purged."}
    except Exception as e:
        logger.error(f"❌ Physical cache purge failed: {e}")
        return {"status": "error", "message": str(e)}


# ── Analysis Routes ────────────────────────────────────────
from fastapi import Request
from api.v1.analyze import router as analyze_router
from api.v1.analyze import analyze_content, AnalyzeRequest
from api.v1.auth import router as auth_router
from api.v1.history import router as history_router
from api.v1.stats import router as stats_router
from api.websocket import router as ws_router
from api.v1.language import router as language_router

# Alias for old/direct endpoint (fixes Flutter mismatch)
@app.post("/analyze", tags=["Analysis"])
async def analyze_alias(request: Request, body: AnalyzeRequest):
    return await analyze_content(request, body)

# Mount static directory for uploads
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)
upload_dir = os.path.join(static_dir, "uploads")
if not os.path.exists(upload_dir):
    os.makedirs(upload_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(analyze_router, prefix="/api/v1", tags=["Analysis"])

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(history_router, prefix="/api/v1", tags=["History"])
app.include_router(stats_router, prefix="/api/v1", tags=["Stats"])
app.include_router(language_router, prefix="/api/v1", tags=["Language"])
app.include_router(ws_router, tags=["WebSocket"])


# ── Request Timing & Global Timeout Middleware ───────────────
@app.middleware("http")
async def timeout_and_timing_middleware(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Incoming Request: {request.method} {request.url.path}")
    
    try:
        # Wrap the entire request in a global 120s timeout
        response = await asyncio.wait_for(call_next(request), timeout=120.0)
        process_time = (time.time() - start_time) * 1000
        response.headers["X-Process-Time-Ms"] = str(round(process_time, 2))
        logger.info(f"Completed Request: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.2f}ms")
        return response
    except asyncio.TimeoutError:
        logger.error(f"GLOBAL TIMEOUT: Request {request.method} {request.url.path} exceeded 120s limit.")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=504,
            content={"detail": "Request timed out after 120 seconds. The analysis is taking too long."}
        )
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(f"Request Failed: {request.url.path} after {process_time:.2f}ms: {e}")
        raise e


if __name__ == "__main__":
    import uvicorn
    # Use the port from settings for local testing parity
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, log_level="info")
