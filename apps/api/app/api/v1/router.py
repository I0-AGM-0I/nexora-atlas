"""
NEXORA ATLAS - v1 Router Aggregator
"""

from fastapi import APIRouter
from app.api.v1.meta import router as meta_router
from app.api.v1.demo import router as demo_router

api_v1_router = APIRouter()

# Mount metadata router
api_v1_router.include_router(meta_router, tags=["System Metadata"])
api_v1_router.include_router(demo_router)
