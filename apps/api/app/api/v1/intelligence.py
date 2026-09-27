"""
NEXORA ATLAS - Intelligence API Router
Exposes offline analysis triggers and engine telemetry status.
Strictly offline: Zero AWS network connections, zero cloud resource mutations.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.intelligence import IntelligenceService
from app.schemas.intelligence import IntelligenceRunResponse, IntelligenceStatusResponse

router = APIRouter(prefix="/intelligence", tags=["Intelligence Engine"])


@router.post("/run", response_model=IntelligenceRunResponse, summary="Execute deterministic intelligence analysis")
async def run_intelligence_analysis(
    org_slug: Optional[str] = Query(None, description="Optional tenant organization slug"),
    session: AsyncSession = Depends(get_db),
) -> IntelligenceRunResponse:
    """
    Executes full offline intelligence analysis:
    Cost Records -> Statistical Baselines -> Anomalies -> Evidence Contracts -> Waste Detection -> Recommendations -> Idempotent Upsert.
    """
    return await IntelligenceService.run_analysis(session, org_slug=org_slug)


@router.get("/status", response_model=IntelligenceStatusResponse, summary="Get intelligence engine status and audit information")
async def get_intelligence_status(
    org_slug: Optional[str] = Query(None, description="Optional tenant organization slug"),
    session: AsyncSession = Depends(get_db),
) -> IntelligenceStatusResponse:
    """
    Returns engine metadata, ruleset version, offline mode guarantee, and active findings.
    """
    return await IntelligenceService.get_status(session, org_slug=org_slug)
