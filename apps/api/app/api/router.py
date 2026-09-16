"""
NEXORA ATLAS - Top-Level API Router
Provides system health probe and mounts versioned APIs.
"""

from fastapi import APIRouter
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import check_database_connection
from app.schemas.common import HealthResponse

root_router = APIRouter()


@root_router.get("/health", response_model=HealthResponse, tags=["Health Probe"])
async def get_health() -> HealthResponse:
    """Primary health check verifying database connectivity and service state."""
    db_health = await check_database_connection()
    is_healthy = db_health.get("status") == "connected"

    return HealthResponse(
        status="healthy" if is_healthy else "degraded",
        service=settings.SERVICE_NAME,
        version=settings.API_VERSION,
        database=db_health.get("status", "disconnected"),
        database_type=db_health.get("type", "unknown"),
    )


# Mount versioned API routes under /api/v1
root_router.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
