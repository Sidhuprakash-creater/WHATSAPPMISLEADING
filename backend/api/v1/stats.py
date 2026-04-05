"""
Dashboard Stats — GET /api/v1/stats
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from db.database import get_db
from db.models import DailyStat, AnalysisRecord

router = APIRouter()

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate statistics for dashboard from DB"""
    
    # Get total stats from DailyStat table
    stats_query = await db.execute(select(func.sum(DailyStat.total_scans), func.sum(DailyStat.fake_detected)))
    result = stats_query.first()
    
    total = result[0] or 0
    fake = result[1] or 0
    
    # Let's count content breakdown
    text_c = await db.execute(select(func.count(AnalysisRecord.id)).where(AnalysisRecord.content_type == "text"))
    url_c = await db.execute(select(func.count(AnalysisRecord.id)).where(AnalysisRecord.content_type == "url"))
    img_c = await db.execute(select(func.count(AnalysisRecord.id)).where(AnalysisRecord.content_type == "image"))
    vid_c = await db.execute(select(func.count(AnalysisRecord.id)).where(AnalysisRecord.content_type == "video"))
    
    return {
        "total_analyses": total,
        "high_risk_count": fake,
        "medium_risk_count": 0, # Could be aggregated later
        "low_risk_count": total - fake,
        "avg_confidence": 85, # placeholder metric
        "avg_processing_ms": 1100, # placeholder metric
        "content_type_breakdown": {
            "text": text_c.scalar() or 0,
            "url": url_c.scalar() or 0,
            "image": img_c.scalar() or 0,
            "video": vid_c.scalar() or 0,
        },
    }
