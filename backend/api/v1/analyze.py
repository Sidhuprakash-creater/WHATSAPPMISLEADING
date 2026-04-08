"""
Main Analysis Endpoint — POST /api/v1/analyze
Accepts text, URL, image, or video and runs the full AI pipeline
"""
import hashlib
import json
import time
import uuid
import logging
from typing import Optional, Any
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from utils.safety_utils import is_safe_text

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Request / Response Models ───────────────────────────────
class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra='allow')
    
    content_type: str = Field(..., pattern="^(text|url|image|video|document)$", description="Type of content")
    text: Optional[str] = Field(None, max_length=50000, description="Text or URL content")
    file_url: Optional[str] = Field(None, description="Image/video URL (Cloudinary)")
    session_id: Optional[str] = Field(None, description="Session ID for history")


class SignalResult(BaseModel):
    label: Optional[str] = None
    prob: Optional[float] = None
    threat: Optional[str] = None
    score: Optional[float] = None
    nsfw: Optional[bool] = None
    ai_generated: Optional[float] = None


class AnalyzeResponse(BaseModel):
    id: str
    verdict: str
    confidence: int
    risk_score: int
    reasons: list[str]
    explanation: Optional[dict] = None   # Rich structured explanation (NEW)
    signals: dict
    remote_url: Optional[str] = None
    processing_ms: int



# ── Main Analyze Endpoint ──────────────────────────────────
@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_content(request: Request, body: AnalyzeRequest):
    """
    Main analysis endpoint. Runs the full AI pipeline:
    1. Check cache (Redis)
    2. Route to appropriate analyzers
    3. Run analyzers in parallel
    4. Fuse scores via AI Wrapper
    5. Return verdict + reasons
    """
    start_time = time.time()
    
    # Validate input
    if body.content_type in ("text", "url") and not body.text:
        raise HTTPException(400, "Text field required for text/url analysis")
    if body.content_type in ("image", "video") and not body.file_url:
        raise HTTPException(400, "file_url required for image/video analysis")
    
    # ── Step 0: Safety Guard ─────────────────────────────
    if body.text and not is_safe_text(body.text):
        logger.warning(f"Offensive content blocked: {body.text[:50]}...")
        raise HTTPException(
            status_code=400, 
            detail="⚠️ Safety Warning: Offensive language is not allowed in MisLEADING. Please remove it to proceed."
        )
    
    # Generate content hash for caching
    content = body.text or body.file_url or ""
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    
    # ── Step 1: Cache Check ─────────────────────────────
    redis = request.app.state.redis
    if redis:
        try:
            cached = await redis.get(f"analysis:{content_hash}")
            if cached:
                result = json.loads(cached)
                result["processing_ms"] = 1  # Cache hit = instant
                return AnalyzeResponse(**result)
        except Exception:
            pass  # Cache miss or error — continue analysis
    
    # ── Step 2: Run AI Pipeline ─────────────────────────
    from ai_wrapper.wrapper import run_full_analysis
    import re

    # Automated URL extraction for full "Scam Shield" coverage
    extracted_url = None
    if body.text:
        # Robust URL extraction regex
        url_match = re.search(r'(https?://[^\s/$.?#].[^\s]*)', body.text)
        if url_match:
            extracted_url = url_match.group(0)
    
    analysis_input = {
        "content_type": body.content_type,
        "text": body.text,
        "url": extracted_url or (body.text if body.content_type == "url" else None),
        "file_url": body.file_url,
        "ml_model": request.app.state.ml_model,
    }
    
    try:
        result = await run_full_analysis(analysis_input)
    except Exception as e:
        logger.error(f"AI Pipeline Crash: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AI Engine Error: {str(e)}")
    
    # ── Step 2.5: Host the file if Base64 (for Cross-User Sync) ──
    remote_url = None
    if body.content_type in ("image", "document") and body.file_url and body.file_url.startswith("data:"):
        try:
            import base64
            import os
            
            # Determine extension
            header, encoded = body.file_url.split(",", 1)
            ext = "jpg"
            if "image/png" in header: ext = "png"
            elif "application/pdf" in header: ext = "pdf"
            
            filename = f"{uuid.uuid4().hex}.{ext}"
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            upload_dir = os.path.join(backend_dir, "static", "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, filename)
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(encoded))
            
            # Construct public URL
            base_url = str(request.base_url).rstrip("/")
            # Safety: If running behind a specific IP/proxy, ensure it matches
            remote_url = f"{base_url}/static/uploads/{filename}"
            logger.info(f"📁 Hosted uploaded {body.content_type} at: {remote_url}")
        except Exception as e:
            logger.error(f"❌ Failed to host file: {e}")
    
    # ── Step 3: Build Response ──────────────────────────
    processing_ms = int((time.time() - start_time) * 1000)
    
    response_data = {
        "id": str(uuid.uuid4()),
        "verdict": result["verdict"],
        "confidence": result["confidence"],
        "risk_score": result["risk_score"],
        "reasons": result["reasons"],
        "explanation": result.get("explanation"),   # Rich structured explanation
        "signals": result["signals"],
        "remote_url": remote_url,
        "processing_ms": processing_ms,
    }

    
    # ── Step 4: Save to Database ──────────────────────────
    from db.database import AsyncSessionLocal
    from db.models import AnalysisRecord, DailyStat
    from datetime import datetime
    import sys
    
    # Run DB insert in background to not block response (using simple new session)
    async def save_to_db(data: dict):
        async with AsyncSessionLocal() as session:
            try:
                # 1. Save History
                record = AnalysisRecord(
                    id=data["id"],
                    content_type=body.content_type,
                    content=str(content)[:1000],  # trim 
                    verdict=data["verdict"],
                    risk_score=data["risk_score"],
                    confidence=data["confidence"],
                    reasons=data["reasons"],
                    raw_signals=data["signals"],
                    processing_ms=data["processing_ms"],
                    client_ip=request.client.host if request.client else None
                )
                session.add(record)
                
                # 2. Update Stats
                today_str = datetime.now().strftime("%Y-%m-%d")
                from sqlalchemy.future import select
                stat_query = await session.execute(select(DailyStat).where(DailyStat.date == today_str))
                stat = stat_query.scalar_one_or_none()
                
                if not stat:
                    stat = DailyStat(date=today_str, total_scans=1, fake_detected=1 if data["risk_score"] > 60 else 0)
                    session.add(stat)
                else:
                    stat.total_scans += 1
                    if data["risk_score"] > 60:
                        stat.fake_detected += 1
                        
                await session.commit()
            except Exception as e:
                logger.error(f"DB Error: {e}")
                
    import asyncio
    asyncio.create_task(save_to_db(response_data))
    
    # ── Step 5: Cache Result ────────────────────────────
    if redis:
        try:
            await redis.setex(
                f"analysis:{content_hash}",
                3600,  # 1 hour TTL
                json.dumps(response_data),
            )
        except Exception:
            pass  # Cache write failure is non-critical
    
    return AnalyzeResponse(**response_data)
