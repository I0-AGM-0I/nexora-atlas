"""
NEXORA ATLAS - Health & Metadata Endpoint Tests
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Verify GET /health returns 200 and expected payload."""
    response = await client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["service"] == "nexora-atlas-api"
    assert data["version"] == "0.1.0"
    assert "database" in data
    assert "database_type" in data


@pytest.mark.asyncio
async def test_meta_endpoint(client: AsyncClient):
    """Verify GET /api/v1/meta returns runtime metadata."""
    response = await client.get("/api/v1/meta")
    assert response.status_code == 200

    data = response.json()
    assert data["api_version"] == "0.1.0"
    assert data["environment"] in ["development", "testing", "staging", "production"]
    assert isinstance(data["demo_mode"], bool)
    assert data["service_name"] == "nexora-atlas-api"
