"""
NEXORA ATLAS - Scenario Service
Read-only exposure of strategic cost scenario simulations.
"""

from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scenario import Scenario, ScenarioChange
from app.services.tenant import TenantContext
from app.schemas.scenario import ScenarioItem, ScenarioChangeItem, ScenarioListResponse


class ScenarioService:
    @classmethod
    async def list_scenarios(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
    ) -> ScenarioListResponse:
        """Returns read-only scenario simulation options for the organization."""
        query = (
            select(Scenario)
            .options(selectinload(Scenario.changes))
            .where(Scenario.org_id == tenant.org_id)
            .order_by(Scenario.monthly_savings.desc())
        )
        result = await session.execute(query)
        scenarios = list(result.scalars().all())

        items: List[ScenarioItem] = []
        for s in scenarios:
            changes = [
                ScenarioChangeItem(
                    id=c.id,
                    scenario_id=c.scenario_id,
                    resource_id=c.resource_id,
                    change_type=c.change_type,
                    current_spec=c.current_spec,
                    proposed_spec=c.proposed_spec,
                    delta_cost=c.delta_cost,
                )
                for c in s.changes
            ]
            items.append(
                ScenarioItem(
                    id=s.id,
                    name=s.name,
                    description=s.description,
                    baseline_monthly_cost=s.baseline_monthly_cost,
                    projected_monthly_cost=s.projected_monthly_cost,
                    monthly_savings=s.monthly_savings,
                    percentage_savings=s.percentage_savings,
                    performance_risk=s.performance_risk,
                    reliability_risk=s.reliability_risk,
                    complexity_level=s.complexity_level,
                    assumptions_json=s.assumptions_json,
                    changes=changes,
                )
            )

        return ScenarioListResponse(scenarios=items)

    @classmethod
    async def simulate_scenario(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        name: str,
        scenario_type: str,
        proposed_changes: List[dict],
        baseline_monthly_cost: Optional[Decimal] = None,
        custom_assumptions: Optional[dict] = None,
        description: Optional[str] = None,
    ):
        """Executes a non-destructive what-if scenario simulation with full constraint validation."""
        from app.models.resource import CloudResource
        from app.services.dashboard import DashboardService
        from app.analytics.scenarios import ScenarioEngine
        from app.analytics.types import ScenarioType as ST

        # If baseline not provided, use current 30-day run rate
        if baseline_monthly_cost is None:
            summary = await DashboardService.get_summary(session, tenant)
            baseline_monthly_cost = summary.monthly_run_rate

        # Fetch resources for constraint checks
        res_q = await session.execute(
            select(CloudResource)
            .options(selectinload(CloudResource.tags))
            .where(CloudResource.account_id.in_(tenant.account_ids))
        )
        resource_map = {
            r.id: {
                "id": r.id,
                "name": r.name,
                "service_name": r.service_name,
                "specs_json": r.specs_json,
                "tags": {t.key: t.value for t in r.tags} if r.tags else {},
            }
            for r in res_q.scalars().all()
        }

        try:
            st_enum = ST(scenario_type.upper())
        except Exception:
            st_enum = ST.CUSTOM

        return ScenarioEngine.simulate_scenario(
            name=name,
            scenario_type=st_enum,
            baseline_monthly_cost=baseline_monthly_cost,
            proposed_changes=proposed_changes,
            resource_map=resource_map,
            custom_assumptions=custom_assumptions,
            description=description,
        )
