"""
NEXORA ATLAS - MIT-WPU Cloud Computing & DevOps CCA 2 Submission Tests
Verifies the three mandatory automated test requirements:
1. Health route: GET /health returns HTTP 200 and healthy operational status.
2. Data mutation: Valid POST /api/v1/integrations/aws/configure creates/modifies data in database.
3. Input validation: Invalid POST to the same endpoint missing required input is rejected with HTTP 422.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.demo import seed_demo_data
from app.models.account import Integration


@pytest_asyncio.fixture(autouse=True)
async def setup_test_estate(db_session: AsyncSession):
    """Seed the database with baseline estate before running CCA submission tests."""
    await seed_demo_data(db_session, reset_first=True)


@pytest.mark.asyncio
async def test_cca_requirement_health_endpoint(client: AsyncClient):
    """
    CCA Requirement: /health endpoint returning a successful health response.
    Verifies HTTP 200, healthy status, service identification, and active database connection.
    """
    response = await client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "nexora-atlas-api"
    assert data["database"] == "connected"
    assert "version" in data
    assert "database_type" in data


@pytest.mark.asyncio
async def test_cca_requirement_post_data_mutation_success(client: AsyncClient, db_session: AsyncSession):
    """
    CCA Requirement: A form that performs a POST request and changes/adds data, with input validation.
    Verifies valid POST /api/v1/integrations/aws/configure:
    - Returns HTTP 200 OK
    - Validates payload structure
    - Successfully persists/updates Integration record in the database
    """
    payload = {
        "role_arn": "arn:aws:iam::123456789012:role/CCAAssessmentReadOnly",
        "external_id": "cca-mit-wpu-ext-id",
        "regions": ["us-east-1", "eu-west-1"],
        "account_name": "CCA Production Core Account",
    }

    response = await client.post("/api/v1/integrations/aws/configure", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["provider_type"] == "AWS"
    assert data["account_name"] == "CCA Production Core Account"
    assert "us-east-1" in data["regions"]
    assert "id" in data

    # Verify server-side data persistence in database
    created_id = data["id"]
    db_result = await db_session.execute(
        select(Integration).where(Integration.id == created_id)
    )
    integration_record = db_result.scalars().first()
    assert integration_record is not None
    assert integration_record.status == "CONFIGURED"
    assert integration_record.provider_type == "AWS"
    assert integration_record.config_json.get("account_name") == "CCA Production Core Account"


@pytest.mark.asyncio
async def test_cca_requirement_post_input_validation_rejection(client: AsyncClient, db_session: AsyncSession):
    """
    CCA Requirement: Invalid input rejected with validation error.
    Verifies that POST /api/v1/integrations/aws/configure missing required role_arn:
    - Returns HTTP 422 Unprocessable Entity
    - Standardized error envelope with VALIDATION_ERROR code
    - Contains validation failure details pointing to 'role_arn'
    - Causes zero database mutations
    """
    invalid_payload = {
        # Missing required 'role_arn' field
        "account_name": "Invalid CCA Test Without Role",
        "regions": ["us-east-1"],
    }

    response = await client.post("/api/v1/integrations/aws/configure", json=invalid_payload)
    assert response.status_code == 422

    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    details = data["error"]["details"]
    assert isinstance(details, list)

    # Assert that validation explicitly caught the missing 'role_arn'
    missing_fields = [
        err["loc"][-1]
        for err in details
        if err.get("type") == "missing"
    ]
    assert "role_arn" in missing_fields

    # Assert no integration record was created with the rejected payload
    db_result = await db_session.execute(
        select(Integration).where(Integration.auth_method == "Invalid CCA Test Without Role")
    )
    records = list(db_result.scalars().all())
    assert len(records) == 0


@pytest.mark.asyncio
async def test_cca_requirement_static_spa_serving(client: AsyncClient):
    """
    CCA Requirement: Static React SPA serving with BrowserRouter fallback.
    Verifies that client-side routes return HTTP 200 and the compiled React HTML.
    """
    for route in ["/", "/dashboard", "/spend", "/scenarios"]:
        response = await client.get(route)
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert '<div id="root">' in response.text


@pytest.mark.asyncio
async def test_cca_requirement_api_route_isolation_json_404(client: AsyncClient):
    """
    CCA Requirement: API route isolation.
    Unknown /api/* routes must return JSON 404, NEVER the HTML index.html fallback.
    """
    for invalid_route in ["/api/v1/nonexistent-endpoint", "/api/invalid-route"]:
        response = await client.get(invalid_route)
        assert response.status_code == 404
        assert "application/json" in response.headers.get("content-type", "")
        data = response.json()
        assert "detail" in data


@pytest.mark.asyncio
async def test_cca_requirement_api_docs_endpoints(client: AsyncClient):
    """
    CCA Requirement: API documentation routes remain intact.
    Verifies that /docs, /openapi.json are accessible and unaffected by SPA catch-all.
    """
    docs_resp = await client.get("/docs")
    assert docs_resp.status_code == 200

    openapi_resp = await client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    data = openapi_resp.json()
    assert "paths" in data

