"""
NEXORA ATLAS - v1 Router Aggregator
"""

from fastapi import APIRouter
from app.api.v1.meta import router as meta_router
from app.api.v1.demo import router as demo_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.spend import router as spend_router
from app.api.v1.anomalies import router as anomalies_router
from app.api.v1.optimization import router as optimization_router
from app.api.v1.resources import router as resources_router
from app.api.v1.scenarios import router as scenarios_router
from app.api.v1.forecast import router as forecast_router
from app.api.v1.intelligence import router as intelligence_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.telemetry import router as telemetry_router
from app.api.v1.ai import router as ai_router

api_v1_router = APIRouter()

# Mount metadata router
api_v1_router.include_router(meta_router, tags=["System Metadata"])
api_v1_router.include_router(demo_router)

# Mount Phase 4 Domain Routers
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(spend_router)
api_v1_router.include_router(anomalies_router)
api_v1_router.include_router(optimization_router)
api_v1_router.include_router(resources_router)
api_v1_router.include_router(scenarios_router)
api_v1_router.include_router(forecast_router)

# Mount Phase 5 Intelligence Router
api_v1_router.include_router(intelligence_router)

# Mount Phase 6 Analytics Router
api_v1_router.include_router(analytics_router)

# Mount Phase 7 Integrations Router
api_v1_router.include_router(integrations_router)

# Mount Phase 8 Operational Telemetry Router
api_v1_router.include_router(telemetry_router)

# Mount Phase 9 AI Explanation Router
api_v1_router.include_router(ai_router)
