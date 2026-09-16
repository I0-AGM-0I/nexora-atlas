"""
NEXORA ATLAS - System Metadata Endpoint
Returns runtime operational configuration and identity.
"""

from fastapi import APIRouter
from app.core.config import settings
from app.schemas.common import MetaResponse

router = APIRouter()


@router.get("/meta", response_model=MetaResponse, summary="Get API runtime metadata")
async def get_metadata() -> MetaResponse:
    return MetaResponse(
        api_version=settings.API_VERSION,
        environment=settings.ENVIRONMENT,
        demo_mode=settings.DEMO_MODE,
        service_name=settings.SERVICE_NAME,
    )
