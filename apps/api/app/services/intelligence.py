"""
NEXORA ATLAS - Intelligence Service
Connects tenant context with deterministic intelligence engine execution.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.tenant import get_tenant_context
from app.intelligence.orchestration.engine import IntelligenceEngine
from app.schemas.intelligence import (
    IntelligenceRunResponse,
    IntelligenceStatusResponse,
    RuleEvaluationResponse,
)


class IntelligenceService:
    """Service layer exposing intelligence pipeline operations."""

    @classmethod
    async def run_analysis(
        cls,
        db: AsyncSession,
        org_slug: Optional[str] = None,
    ) -> IntelligenceRunResponse:
        """Executes full offline deterministic analysis for the tenant organization."""
        tenant = await get_tenant_context(db, org_slug)
        result = await IntelligenceEngine.run(db, organization_id=tenant.org_id)

        eval_responses = [
            RuleEvaluationResponse(
                rule_id=e.rule_id,
                rule_type=e.rule_type,
                status=e.status.value if hasattr(e.status, "value") else str(e.status),
                skip_reason=e.skip_reason,
                findings_count=e.findings_count,
            )
            for e in result.rule_evaluations
        ]

        return IntelligenceRunResponse(
            run_id=result.run_id,
            organization_id=result.organization_id,
            ruleset_version=result.ruleset_version,
            started_at=result.started_at,
            completed_at=result.completed_at,
            duration_ms=result.duration_ms,
            anomalies_detected=result.anomalies_detected,
            opportunities_found=result.opportunities_found,
            recommendations_generated=result.recommendations_generated,
            potential_monthly_savings=result.potential_monthly_savings,
            potential_annual_savings=result.potential_annual_savings,
            rule_evaluations=eval_responses,
        )

    @classmethod
    async def get_status(
        cls,
        db: AsyncSession,
        org_slug: Optional[str] = None,
    ) -> IntelligenceStatusResponse:
        """Returns intelligence status, active findings, and addressable savings."""
        tenant = await get_tenant_context(db, org_slug)
        status_data = await IntelligenceEngine.get_status(db, organization_id=tenant.org_id)

        return IntelligenceStatusResponse(
            ruleset_version=status_data["ruleset_version"],
            status=status_data["status"],
            last_run_at=status_data["last_run_at"],
            last_run_id=status_data["last_run_id"],
            active_anomalies_count=status_data["active_anomalies_count"],
            active_opportunities_count=status_data["active_opportunities_count"],
            addressable_monthly_savings=status_data["addressable_monthly_savings"],
            addressable_annual_savings=status_data["addressable_annual_savings"],
            is_offline_mode=status_data["is_offline_mode"],
            aws_network_disabled=status_data["aws_network_disabled"],
        )
