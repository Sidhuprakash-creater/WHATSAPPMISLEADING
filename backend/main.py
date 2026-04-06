"""
MisLEADING — FastAPI Application Factory
Main entry point for the backend API server
"""
import os
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


# ── Lifespan (startup/shutdown events) ──────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB, Load ML model at startup, cleanup on shutdown"""
    logger.info("🚀 Starting MisLEADING API Server...")
    
    # Initialize Database
    try:
        from db.database import engine, Base
        import db.models  # Import to register tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
    
    # Load ML model if exists
    model_path = os.path.join(os.path.dirname(__file__), "ml", "model.pkl")
    if os.path.exists(model_path):
        import joblib
        app.state.ml_model = joblib.load(model_path)
        logger.info("✅ ML Model loaded successfully")
    else:
        app.state.ml_model = None
        logger.warning("⚠️ ML Model not found — text analysis will use LLM only")
    
    # Redis connection (optional — graceful fallback)
    try:
        import redis.asyncio as aioredis
        app.state.redis = aioredis.from_url(
            settings.REDIS_URL, 
            decode_responses=True
        )
        await app.state.redis.ping()
        logger.info("✅ Redis connected")
    except Exception:
        app.state.redis = None
        logger.warning("⚠️ Redis not available — caching disabled")
    
    # Initialize Fact Check Engine
    try:
        from analyzers.fact_checker import engine as fact_engine
        fact_engine.initialize()
    except Exception as e:
        logger.error(f"❌ Failed to load fact check engine: {e}")
    
    yield  # App runs
    
    # Cleanup
    if app.state.redis:
        await app.state.redis.close()
    logger.info("🛑 MisLEADING API Server stopped")


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


# ── Import and register routers ────────────────────────────
from api.v1.analyze import router as analyze_router
from api.v1.auth import router as auth_router
from api.v1.history import router as history_router
from api.v1.stats import router as stats_router
from api.websocket import router as ws_router
from api.v1.language import router as language_router

app.include_router(analyze_router, prefix="/api/v1", tags=["Analysis"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(history_router, prefix="/api/v1", tags=["History"])
app.include_router(stats_router, prefix="/api/v1", tags=["Stats"])
app.include_router(language_router, prefix="/api/v1", tags=["Language"])
app.include_router(ws_router, tags=["WebSocket"])


# ── Request Timing Middleware ───────────────────────────────
@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = str(round(process_time, 2))
    return response
