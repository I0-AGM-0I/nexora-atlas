"""
NEXORA ATLAS - Common API Schemas
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="System health state: healthy | degraded | unhealthy")
    service: str = Field(..., description="Name of the running service")
    version: str = Field(..., description="Semantic version of the application")
    database: str = Field(..., description="Connection status: connected | disconnected")
    database_type: str = Field(..., description="Target database engine: postgresql | sqlite")


class MetaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    api_version: str = Field(..., description="API semantic version")
    environment: str = Field(..., description="Active environment name (e.g. development, production)")
    demo_mode: bool = Field(..., description="Whether demo mode with synthetic data is active")
    service_name: str = Field(..., description="Canonical service identity")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
