"""
NEXORA ATLAS - Database Connection & Session Management
Provides dual-engine support: PostgreSQL (canonical production) and SQLite (zero-Docker fallback).
"""

from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import settings
from app.core.logging import logger

connect_args = {}
if settings.is_sqlite:
    connect_args["check_same_thread"] = False

# Create asynchronous engine
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for injecting async database sessions into FastAPI route handlers."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session rollback due to exception: {e}")
            raise
        finally:
            await session.close()


async def check_database_connection() -> dict:
    """Diagnostic health check verifying active database connectivity."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {
            "status": "connected",
            "type": "sqlite" if settings.is_sqlite else "postgresql",
        }
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return {
            "status": "disconnected",
            "type": "sqlite" if settings.is_sqlite else "postgresql",
            "error": str(e),
        }
