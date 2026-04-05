"""
Database Models (SQLAlchemy)
Defines the schema for storing analysis history and system usage
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from datetime import datetime, timezone
from db.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class AnalysisRecord(Base):
    __tablename__ = "analysis_history"

    id = Column(String(36), primary_key=True, index=True)
    content_type = Column(String(20), index=True)  # text, url, image, video
    content = Column(String)  # The text or URL or file path
    
    verdict = Column(String(50), index=True)  # High Risk, Medium Risk, Low Risk
    risk_score = Column(Integer)
    confidence = Column(Integer)
    
    reasons = Column(JSON)  # List of string reasons
    raw_signals = Column(JSON)  # Store entire raw AI wrapper output for debug
    
    processing_ms = Column(Integer)
    client_ip = Column(String(50), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)

class DailyStat(Base):
    """Aggregated stats for the Admin Dashboard to keep charts fast"""
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), unique=True, index=True)  # YYYY-MM-DD
    total_scans = Column(Integer, default=0)
    fake_detected = Column(Integer, default=0)
    avg_processing_time = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), default=utc_now)
