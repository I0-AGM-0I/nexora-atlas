"""
NEXORA ATLAS - Scenarios API Router
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.tenant import get_tenant_context
from app.services.scenario import ScenarioService
from app.schemas.scenario import ScenarioListResponse, ScenarioSimulationRequest
from app.analytics.models import ScenarioSimulationResult

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.get("", response_model=ScenarioListResponse, summary="List strategic cost simulation scenarios")
async def list_scenarios(
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
) -> ScenarioListResponse:
    tenant = await get_tenant_context(session, org_slug)
    return await ScenarioService.list_scenarios(session, tenant)


@router.post("/simulate", response_model=ScenarioSimulationResult, summary="Simulate a what-if architecture optimization scenario")
async def simulate_scenario(
    req: ScenarioSimulationRequest,
    org_slug: Optional[str] = Query(None, description="Optional tenant slug"),
    session: AsyncSession = Depends(get_db),
) -> ScenarioSimulationResult:
    tenant = await get_tenant_context(session, org_slug)
    return await ScenarioService.simulate_scenario(
        session=session,
        tenant=tenant,
        name=req.name,
        scenario_type=req.scenario_type,
        proposed_changes=req.proposed_changes,
        baseline_monthly_cost=req.baseline_monthly_cost,
        custom_assumptions=req.custom_assumptions,
        description=req.description,
    )
