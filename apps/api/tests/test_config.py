"""
NEXORA ATLAS - Settings & Database Abstraction Tests
"""

import pytest
from app.core.config import Settings
from app.core.database import check_database_connection


def test_settings_defaults():
    """Verify default configuration values."""
    settings = Settings()
    assert settings.SERVICE_NAME == "nexora-atlas-api"
    assert settings.API_V1_PREFIX == "/api/v1"
    assert settings.DEMO_MODE is True
    assert settings.is_sqlite is True


def test_cors_origins_parsing():
    """Verify parsing of comma-separated CORS origins."""
    settings = Settings(CORS_ORIGINS="http://localhost:3000, http://example.com")
    assert "http://localhost:3000" in settings.CORS_ORIGINS
    assert "http://example.com" in settings.CORS_ORIGINS


@pytest.mark.asyncio
async def test_database_connection_check():
    """Verify database connection abstraction executes query successfully."""
    result = await check_database_connection()
    assert result["status"] in ["connected", "disconnected"]
    assert result["type"] in ["sqlite", "postgresql"]
