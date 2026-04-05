"""
Database configuration and session management
Uses SQLAlchemy with async support (aiosqlite for local dev / asyncpg for prod)
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

# Create Async Engine
# Check if using SQLite. If yes, add special args to prevent threading issues
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=False,
    connect_args=connect_args
)

# Async Session Factory
AsyncSessionLocal = sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    """Dependency for FastAPI routes to get DB session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
