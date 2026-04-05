"""
Analysis History — GET /api/v1/history
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# In-memory storage for hackathon (replace with PostgreSQL later)
analysis_history: list[dict] = []


class HistoryItem(BaseModel):
    id: str
    content_type: str
    verdict: str
    confidence: int
    created_at: str


@router.get("/history")
async def get_history(limit: int = 20, offset: int = 0):
    """Get paginated analysis history"""
    return {
        "total": len(analysis_history),
        "items": analysis_history[offset:offset + limit],
    }
