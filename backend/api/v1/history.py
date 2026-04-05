"""
Analysis History — GET /api/v1/history
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from db.database import get_db
from db.models import AnalysisRecord
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

class HistoryItem(BaseModel):
    id: str
    content_type: str
    content: Optional[str] = None
    verdict: str
    confidence: int
    risk_score: int
    created_at: datetime
    
    class Config:
        orm_mode = True

@router.get("/history")
async def get_history(
    limit: int = 20, 
    offset: int = 0, 
    db: AsyncSession = Depends(get_db)
):
    """Get paginated analysis history from Database"""
    # Count total
    total_query = await db.execute(select(func.count(AnalysisRecord.id)))
    total = total_query.scalar()
    
    # Fetch Items
    query = select(AnalysisRecord).order_by(AnalysisRecord.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "total": total,
        "items": items,
    }
