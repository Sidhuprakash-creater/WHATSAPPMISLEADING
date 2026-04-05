"""
Dashboard Stats — GET /api/v1/stats
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/stats")
async def get_stats():
    """Aggregate statistics for dashboard"""
    # Placeholder stats (will be computed from DB later)
    return {
        "total_analyses": 0,
        "high_risk_count": 0,
        "medium_risk_count": 0,
        "low_risk_count": 0,
        "avg_confidence": 0,
        "avg_processing_ms": 0,
        "top_domains": [],
        "content_type_breakdown": {
            "text": 0,
            "url": 0,
            "image": 0,
            "video": 0,
        },
    }
