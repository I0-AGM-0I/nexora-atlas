"""
NEXORA ATLAS - Pytest Configuration & Test Fixtures
"""

import os
import tempfile
from pathlib import Path
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.database import get_db
from app.models.base import Base


def _ensure_static_dir():
    """Ensure static SPA serving can be tested even if apps/web/dist has not been pre-built."""
    _web_dist = Path(__file__).resolve().parent.parent.parent / "apps" / "web" / "dist"
    _legacy_dist = Path(__file__).resolve().parent.parent / "web" / "dist"
    if not os.environ.get("STATIC_DIR") and not _web_dist.is_dir() and not _legacy_dist.is_dir():
        _fallback_dist = Path(tempfile.gettempdir()) / "nexora_atlas_test_spa_dist"
        _fallback_dist.mkdir(parents=True, exist_ok=True)
        _test_index = _fallback_dist / "index.html"
        if not _test_index.is_file():
            _test_index.write_text(
                '<!DOCTYPE html><html><head><title>NEXORA ATLAS</title></head><body><div id="root"></div></body></html>',
                encoding="utf-8",
            )
        os.environ["STATIC_DIR"] = str(_fallback_dist)


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession:
    """Provides a fresh isolated in-memory test database session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    """Provides an async HTTP test client with database dependency override."""
    _ensure_static_dir()
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
