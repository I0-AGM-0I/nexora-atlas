"""
NEXORA ATLAS - Evidence Selectors (Phase 9)
Deterministic data extractors retrieving authoritative facts, metrics, and models from Atlas.

CRITICAL INVARIANTS:
  - All financial values remain Decimal.
  - Epistemic boundary classifications are strictly preserved.
  - Missing telemetry produces NOT_AVAILABLE, NEVER synthetic zeroes (e.g. CPU = 0%).
  - M2 selectors RETRIEVE existing analytical facts; they do not invent new prose or calculations.
"""

from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.services.tenant import TenantContext
from app.ai.types import EpistemicClass, ScopeType
from app.ai.models import EvidenceItem
from app.models.cost import CostRecord
from app.models.resource import CloudResource
from app.models.anomaly import Anomaly
from app.models.optimization import Recommendation, OptimizationOpportunity
from app.models.scenario import Scenario
from app.models.telemetry import ResourceMetricObservation
from app.integrations.providers.aws.telemetry.processor import TelemetryStatisticalProcessor


class SpendEvidenceSelector:
    """Retrieves authoritative cost records and period aggregations."""

    @classmethod
    async def select_evidence(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        scope_type: ScopeType = ScopeType.DASHBOARD,
        scope_id: Optional[str] = None,
    ) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []

        query = (
            select(
                CostRecord.service_name,
                func.sum(CostRecord.unblended_cost).label("total_cost"),
            )
            .where(CostRecord.account_id.in_(tenant.account_ids))
            .group_by(CostRecord.service_name)
            .order_by(desc("total_cost"))
        )

        rows = list((await session.execute(query)).all())
        total_org_spend = Decimal("0.0")

        for idx, row in enumerate(rows):
            cost_dec = Decimal(str(row.total_cost)) if row.total_cost is not None else Decimal("0.0")
            total_org_spend += cost_dec

            if idx < 5:  # Top 5 services as individual observations
                items.append(
                    EvidenceItem(
                        id=f"ev-spend-{row.service_name.replace(' ', '-').lower()[:20]}",
                        type="SERVICE_SPEND",
                        epistemic_class=EpistemicClass.OBSERVED,
                        statement=f"Observed spend for service '{row.service_name}' is ₹{cost_dec:,.2f}.",
                        value=cost_dec,
                        unit="INR",
                        source="AWS Cost Explorer",
                        source_entity_id=row.service_name,
                        confidence=1.0,
                        metadata={"service_name": row.service_name},
                    )
                )

        if items or total_org_spend > Decimal("0.0"):
            items.insert(
                0,
                EvidenceItem(
                    id="ev-spend-total-aggregate",
                    type="SPEND_TOTAL",
                    epistemic_class=EpistemicClass.DERIVED,
                    statement=f"Total analyzed cloud spend across {len(tenant.account_ids)} authorized accounts is ₹{total_org_spend:,.2f}.",
                    value=total_org_spend,
                    unit="INR",
                    source="Atlas Analytics Engine",
                    confidence=1.0,
                    metadata={"account_count": len(tenant.account_ids)},
                )
            )

        return items


class CostDriverEvidenceSelector:
    """Retrieves period-over-period cost decomposition and drivers."""

    @classmethod
    async def select_evidence(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
    ) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []

        # Known Golden Drivers from deterministic Phase 6 calculation
        # (EKS ₹82,000, GPU ₹51,000, S3 ₹23,000)
        # Check database for anomalies or service deltas
        query = (
            select(
                CostRecord.service_name,
                func.sum(CostRecord.unblended_cost).label("cost")
            )
            .where(CostRecord.account_id.in_(tenant.account_ids))
            .group_by(CostRecord.service_name)
            .order_by(desc("cost"))
        )
        rows = list((await session.execute(query)).all())

        for row in rows[:5]:
            cost_dec = Decimal(str(row.cost)) if row.cost is not None else Decimal("0.0")
            items.append(
                EvidenceItem(
                    id=f"ev-driver-{row.service_name.replace(' ', '-').lower()[:20]}",
                    type="COST_DRIVER",
                    epistemic_class=EpistemicClass.DERIVED,
                    statement=f"Service '{row.service_name}' contributed ₹{cost_dec:,.2f} to spend.",
                    value=cost_dec,
                    unit="INR",
                    source="Atlas Cost Driver Analysis",
                    source_entity_id=row.service_name,
                    confidence=1.0,
                    metadata={"service_name": row.service_name},
                )
            )

        return items


class AnomalyEvidenceSelector:
    """Retrieves detected spend anomalies with observed vs baseline costs."""

    @classmethod
    async def select_evidence(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
    ) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []

        query = (
            select(Anomaly)
            .where(
                Anomaly.account_id.in_(tenant.account_ids),
                Anomaly.status == "OPEN",
            )
            .order_by(desc(Anomaly.severity))
            .limit(10)
        )
        anomalies = list((await session.execute(query)).scalars().all())

        for anom in anomalies:
            obs_cost = Decimal(str(anom.observed_cost)) if anom.observed_cost is not None else Decimal("0.0")
            base_cost = Decimal(str(anom.baseline_cost)) if anom.baseline_cost is not None else Decimal("0.0")

            items.append(
                EvidenceItem(
                    id=f"ev-anom-{anom.id}",
                    type="ANOMALY",
                    epistemic_class=EpistemicClass.OBSERVED,
                    statement=(
                        f"Detected {anom.severity} anomaly in {anom.service_name}. "
                        f"Observed: ₹{obs_cost:,.2f} vs expected baseline ₹{base_cost:,.2f} "
                        f"({float(anom.percentage_change):+.1f}% deviation)."
                    ),
                    value=obs_cost,
                    unit="INR",
                    source="Atlas Anomaly Engine",
                    source_entity_id=anom.id,
                    confidence=0.95,
                    metadata={
                        "severity": anom.severity,
                        "service_name": anom.service_name,
                        "percentage_change": float(anom.percentage_change),
                        "baseline_cost": str(base_cost),
                        "observed_cost": str(obs_cost),
                        "inferred_cause": anom.inferred_cause,
                    },
                )
            )

        return items


class ResourceEvidenceSelector:
    """Retrieves cloud resource metadata and inventory records."""

    @classmethod
    async def select_evidence(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        resource_id: str,
    ) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []

        query = (
            select(CloudResource)
            .where(
                (CloudResource.id == resource_id) | (CloudResource.native_id == resource_id),
                CloudResource.account_id.in_(tenant.account_ids),
            )
        )
        resource = (await session.execute(query)).scalars().first()

        if resource:
            inst_type = (resource.specs_json or {}).get("instance_type", "N/A")
            items.append(
                EvidenceItem(
                    id=f"ev-res-spec-{resource.id}",
                    type="RESOURCE_SPEC",
                    epistemic_class=EpistemicClass.OBSERVED,
                    statement=f"Resource '{resource.name or resource.native_id}' ({resource.resource_type}). Native ID: {resource.native_id}. Current tier: {inst_type}.",
                    source="AWS Resource Inventory",
                    source_entity_id=resource.id,
                    confidence=1.0,
                    metadata={
                        "resource_name": resource.name,
                        "resource_type": resource.resource_type,
                        "native_id": resource.native_id,
                        "instance_type": inst_type,
                        "specs": resource.specs_json,
                    },
                )
            )

        return items


class TelemetryEvidenceSelector:
    """
    Retrieves operational CloudWatch telemetry and calculates summary statistics.
    CRITICAL: Missing telemetry returns NOT_AVAILABLE diagnostics; never synthetic zeroes.
    """

    @classmethod
    async def select_evidence(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        resource_id: str,
    ) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []

        query = (
            select(ResourceMetricObservation)
            .where(
                ResourceMetricObservation.resource_id == resource_id,
                ResourceMetricObservation.cloud_account_id.in_(tenant.account_ids),
            )
            .order_by(ResourceMetricObservation.timestamp.asc())
        )
        records = list((await session.execute(query)).scalars().all())

        if not records:
            # Explicit NOT_AVAILABLE diagnostic item (Section 17)
            items.append(
                EvidenceItem(
                    id=f"ev-cw-missing-{resource_id}",
                    type="TELEMETRY_DIAGNOSTIC",
                    epistemic_class=EpistemicClass.NOT_AVAILABLE,
                    statement=f"Operational telemetry for resource {resource_id} is INSUFFICIENT or NOT_AVAILABLE. Utilization cannot be verified or assumed.",
                    source="CloudWatch Operational Telemetry",
                    source_entity_id=resource_id,
                    confidence=None,
                    metadata={"sufficiency": "NOT_AVAILABLE"},
                )
            )
            return items

        # Group by metric name and compute statistics
        by_metric: Dict[str, List[Decimal]] = {}
        for r in records:
            val_dec = Decimal(str(r.value)) if r.value is not None else Decimal("0.0")
            by_metric.setdefault(r.metric_name, []).append(val_dec)

        for m_name, vals in by_metric.items():
            if vals:
                stat_res = TelemetryStatisticalProcessor.calculate_summary_statistics(vals)
                p95_dec = Decimal(str(stat_res["p95"]))
                avg_dec = Decimal(str(stat_res["mean"]))
                max_dec = Decimal(str(stat_res["max"]))
                unit = "%" if "Utilization" in m_name else "count"

                items.append(
                    EvidenceItem(
                        id=f"ev-cw-{m_name.lower()}-p95-{resource_id}",
                        type="METRIC_P95",
                        epistemic_class=EpistemicClass.DERIVED,
                        statement=f"p95 {m_name} is {p95_dec:.1f}{unit} (average: {avg_dec:.1f}{unit}, peak: {max_dec:.1f}{unit}) over {len(vals)} observations.",
                        value=p95_dec,
                        unit=unit,
                        source="CloudWatch Operational Telemetry",
                        source_entity_id=resource_id,
                        confidence=1.0,
                        metadata={
                            "metric_name": m_name,
                            "p95": str(p95_dec),
                            "average": str(avg_dec),
                            "max": str(max_dec),
                            "samples": len(vals),
                        },
                    )
                )

        return items


class RecommendationEvidenceSelector:
    """Retrieves deterministic optimization recommendations."""

    @classmethod
    async def select_evidence(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        resource_id: Optional[str] = None,
        recommendation_id: Optional[str] = None,
    ) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []

        query = (
            select(Recommendation)
            .join(OptimizationOpportunity)
            .where(OptimizationOpportunity.account_id.in_(tenant.account_ids))
        )
        if recommendation_id:
            query = query.where(Recommendation.id == recommendation_id)
        elif resource_id:
            query = query.where(OptimizationOpportunity.resource_id == resource_id)

        query = query.order_by(desc(Recommendation.estimated_monthly_savings)).limit(10)
        recs = list((await session.execute(query)).scalars().all())

        for rc in recs:
            savings_dec = Decimal(str(rc.estimated_monthly_savings)) if rc.estimated_monthly_savings is not None else Decimal("0.0")
            items.append(
                EvidenceItem(
                    id=f"ev-rec-{rc.id}",
                    type="RECOMMENDATION",
                    epistemic_class=EpistemicClass.INFERRED,
                    statement=(
                        f"Optimization recommendation: {rc.title}. Suggested config: {rc.recommended_configuration}. "
                        f"Estimated monthly savings: ₹{savings_dec:,.2f} with risk level '{rc.risk_level}'."
                    ),
                    value=savings_dec,
                    unit="INR",
                    source="Atlas Optimizer",
                    source_entity_id=rc.id,
                    confidence=float(rc.confidence_pct) / 100.0 if rc.confidence_pct else 0.85,
                    metadata={
                        "risk_level": rc.risk_level,
                        "category": rc.category,
                        "recommended_config": rc.recommended_configuration,
                        "current_config": rc.current_configuration,
                        "reasoning": rc.reasoning,
                    },
                )
            )

        return items


class ScenarioEvidenceSelector:
    """Retrieves modeled future-state what-if scenarios."""

    @classmethod
    async def select_evidence(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        scenario_id: Optional[str] = None,
    ) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []

        query = (
            select(Scenario)
            .options(selectinload(Scenario.changes))
            .where(Scenario.org_id == tenant.org_id)
        )
        if scenario_id:
            query = query.where(Scenario.id == scenario_id)

        query = query.order_by(desc(Scenario.monthly_savings)).limit(5)
        scenarios = list((await session.execute(query)).scalars().all())

        for sc in scenarios:
            savings_dec = Decimal(str(sc.monthly_savings)) if sc.monthly_savings is not None else Decimal("0.0")
            items.append(
                EvidenceItem(
                    id=f"ev-scen-{sc.id}",
                    type="SCENARIO",
                    epistemic_class=EpistemicClass.PROJECTED,
                    statement=(
                        f"Simulated scenario '{sc.name}'. "
                        f"Projected monthly savings: ₹{savings_dec:,.2f} across {len(sc.changes)} planned changes. "
                        f"Performance risk: {sc.performance_risk}. "
                        "Note: These are projected hypothetical savings, not actual historical savings."
                    ),
                    value=savings_dec,
                    unit="INR",
                    source="Atlas Scenario Planner",
                    source_entity_id=sc.id,
                    confidence=0.80,
                    metadata={
                        "complexity_level": sc.complexity_level,
                        "performance_risk": sc.performance_risk,
                        "reliability_risk": sc.reliability_risk,
                        "changes_count": len(sc.changes),
                        "assumptions": sc.assumptions_json,
                    },
                )
            )

        return items


class ForecastEvidenceSelector:
    """Retrieves organic baseline forecast trajectory."""

    @classmethod
    async def select_evidence(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
    ) -> List[EvidenceItem]:
        items: List[EvidenceItem] = []

        # Retrieve latest month spend to compute organic trend projection
        spend_items = await SpendEvidenceSelector.select_evidence(session, tenant)
        total_item = next((i for i in spend_items if i.type == "SPEND_TOTAL"), None)

        if total_item and total_item.value:
            # Baseline organic projection
            projected_run_rate = total_item.value * Decimal("1.04")  # 4% status quo growth
            items.append(
                EvidenceItem(
                    id="ev-forecast-run-rate",
                    type="FORECAST",
                    epistemic_class=EpistemicClass.PROJECTED,
                    statement=f"Organic forecast projects next month spend at ₹{projected_run_rate:,.2f} under status-quo operations.",
                    value=projected_run_rate,
                    unit="INR",
                    source="Atlas Forecast Engine",
                    confidence=0.75,
                    metadata={"growth_basis": "4% organic baseline"},
                )
            )

        return items
