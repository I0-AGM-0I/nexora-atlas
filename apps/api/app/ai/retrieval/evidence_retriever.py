"""
NEXORA ATLAS - Deterministic Evidence Retriever (Phase 9)
Collects authoritative facts, metrics, and models from Atlas engines.
Strictly tenant-scoped; attaches DataFreshness and preserves epistemic classes.
"""

from decimal import Decimal
from datetime import datetime, date, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.tenant import TenantContext
from app.ai.types import EpistemicClass, ScopeType, QuestionCategory, DataFreshnessStatus
from app.ai.models import EvidenceItem, EvidencePackage, DataFreshness
from app.models.cost import CostRecord
from app.models.resource import CloudResource
from app.models.account import CloudAccount
from app.models.anomaly import Anomaly
from app.models.optimization import OptimizationOpportunity, Recommendation
from app.models.scenario import Scenario
from app.models.telemetry import ResourceMetricObservation
from app.integrations.providers.aws.telemetry.processor import TelemetryStatisticalProcessor


class EvidenceRetriever:
    """
    Assembles authoritative evidence for a query and scope.
    Calls existing database queries and domain models without duplicating business logic.
    """

    @classmethod
    async def assess_freshness(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
    ) -> DataFreshness:
        """Evaluates timestamps of latest available cost records, telemetry, and resources."""
        now = datetime.now(timezone.utc)

        # 1. Latest cost date
        cost_q = (
            select(func.max(CostRecord.usage_date))
            .where(CostRecord.account_id.in_(tenant.account_ids))
        )
        cost_res = await session.execute(cost_q)
        max_cost_date: Optional[date] = cost_res.scalar_one_or_none()

        # 2. Latest CloudWatch telemetry
        cw_q = (
            select(func.max(ResourceMetricObservation.retrieved_at))
            .where(ResourceMetricObservation.cloud_account_id.in_(tenant.account_ids))
        )
        cw_res = await session.execute(cw_q)
        max_cw_time: Optional[datetime] = cw_res.scalar_one_or_none()

        # 3. Latest resource update
        res_q = (
            select(func.max(CloudResource.updated_at))
            .where(CloudResource.account_id.in_(tenant.account_ids))
        )
        res_res = await session.execute(res_q)
        max_res_time: Optional[datetime] = res_res.scalar_one_or_none()

        # Determine status and summary
        cw_age_str = "No telemetry recorded"
        if max_cw_time:
            if max_cw_time.tzinfo is None:
                max_cw_time = max_cw_time.replace(tzinfo=timezone.utc)
            mins = int((now - max_cw_time).total_seconds() / 60)
            cw_age_str = f"{mins} minutes ago" if mins < 120 else f"{mins // 60} hours ago"

        cost_str = str(max_cost_date) if max_cost_date else "No cost data"

        status_enum = DataFreshnessStatus.UNKNOWN
        if max_cost_date and max_cw_time:
            status_enum = DataFreshnessStatus.FRESH

        summary = f"Cost data through: {cost_str}. CloudWatch telemetry retrieved: {cw_age_str}."

        return DataFreshness(
            cloudwatch_retrieved_at=max_cw_time,
            cost_data_through=cost_str,
            resource_inventory_synced_at=max_res_time,
            status=status_enum,
            freshness_summary=summary,
        )

    @classmethod
    async def retrieve_evidence(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        scope_type: ScopeType,
        scope_id: Optional[str] = None,
        category: QuestionCategory = QuestionCategory.SPEND_OVERVIEW,
        detected_services: Optional[List[str]] = None,
    ) -> EvidencePackage:
        """
        Gathers evidence across domain tables according to the authorized scope and category.
        """
        freshness = await cls.assess_freshness(session, tenant)

        observations: List[EvidenceItem] = []
        derived_metrics: List[EvidenceItem] = []
        inferences: List[EvidenceItem] = []
        recommendations: List[EvidenceItem] = []
        scenarios: List[EvidenceItem] = []
        telemetry: List[EvidenceItem] = []
        limitations: List[str] = []

        # 1. SCOPE: RESOURCE
        if scope_type == ScopeType.RESOURCE and scope_id:
            res_q = (
                select(CloudResource)
                .where(
                    (CloudResource.id == scope_id) | (CloudResource.native_id == scope_id),
                    CloudResource.account_id.in_(tenant.account_ids),
                )
            )
            r = (await session.execute(res_q)).scalars().first()
            if r:
                inst_type = (r.specs_json or {}).get("instance_type", "N/A")
                observations.append(
                    EvidenceItem(
                        id=f"res-spec-{r.id}",
                        type="RESOURCE_SPEC",
                        epistemic_class=EpistemicClass.OBSERVED,
                        statement=f"Resource '{r.name or r.native_id}' ({r.resource_type}). Native ID: {r.native_id}. Current type/tier: {inst_type}.",
                        source="AWS Resource Inventory",
                        source_entity_id=r.id,
                        confidence=1.0,
                        metadata={
                            "resource_name": r.name,
                            "resource_type": r.resource_type,
                            "native_id": r.native_id,
                            "instance_type": inst_type,
                            "specs": r.specs_json,
                        },
                    )
                )

                # Fetch CloudWatch telemetry for this resource
                obs_q = (
                    select(ResourceMetricObservation)
                    .where(
                        ResourceMetricObservation.resource_id == r.id,
                        ResourceMetricObservation.cloud_account_id.in_(tenant.account_ids),
                    )
                    .order_by(ResourceMetricObservation.timestamp.asc())
                )
                obs_records = list((await session.execute(obs_q)).scalars().all())

                if not obs_records:
                    limitations.append(
                        f"Operational telemetry for resource {r.resource_id} is INSUFFICIENT or NOT_AVAILABLE. "
                        "Utilization cannot be verified or assumed."
                    )
                else:
                    # Group by metric name and calculate derived p95 and average
                    by_metric: Dict[str, List[float]] = {}
                    for o in obs_records:
                        by_metric.setdefault(o.metric_name, []).append(float(o.value))

                    for m_name, vals in by_metric.items():
                        if vals:
                            stat_res = TelemetryStatisticalProcessor.calculate_summary_statistics(
                                [Decimal(str(v)) for v in vals]
                            )
                            p95_val = float(stat_res["p95"])
                            avg_val = float(stat_res["mean"])
                            max_val = float(stat_res["max"])
                            unit = "%" if "Utilization" in m_name else "count"

                            telemetry.append(
                                EvidenceItem(
                                    id=f"cw-{m_name.lower()}-p95-{r.id}",
                                    type="METRIC_P95",
                                    epistemic_class=EpistemicClass.DERIVED,
                                    statement=f"p95 {m_name} is {p95_val:.1f}{unit} (average: {avg_val:.1f}{unit}, peak: {max_val:.1f}{unit}) over {len(vals)} observations.",
                                    value=p95_val,
                                    unit=unit,
                                    source="CloudWatch Operational Telemetry",
                                    source_entity_id=r.id,
                                    confidence=1.0,
                                    metadata={"p95": p95_val, "average": avg_val, "samples": len(vals)},
                                )
                            )

                # Check for recommendations targeting this resource
                rec_q = (
                    select(Recommendation)
                    .join(OptimizationOpportunity)
                    .where(
                        OptimizationOpportunity.resource_id == r.id,
                        OptimizationOpportunity.account_id.in_(tenant.account_ids),
                    )
                )
                recs = list((await session.execute(rec_q)).scalars().all())
                for rc in recs:
                    recommendations.append(
                        EvidenceItem(
                            id=f"rec-{rc.id}",
                            type="RECOMMENDATION",
                            epistemic_class=EpistemicClass.INFERRED,
                            statement=f"Optimization recommendation: {rc.title}. Suggested config: {rc.recommended_configuration}. Estimated monthly savings: ₹{float(rc.estimated_monthly_savings):,.0f}.",
                            value=float(rc.estimated_monthly_savings),
                            unit="INR",
                            source="Atlas Optimizer",
                            source_entity_id=rc.id,
                            confidence=float(rc.confidence_pct) / 100.0 if rc.confidence_pct else 0.85,
                            metadata={
                                "risk_level": rc.risk_level,
                                "category": rc.category,
                                "recommended_config": rc.recommended_configuration,
                            },
                        )
                    )

        # 2. SCOPE: RECOMMENDATION
        elif scope_type == ScopeType.RECOMMENDATION and scope_id:
            rec_q = (
                select(Recommendation)
                .join(OptimizationOpportunity)
                .options(selectinload(Recommendation.opportunity))
                .where(
                    Recommendation.id == scope_id,
                    OptimizationOpportunity.account_id.in_(tenant.account_ids),
                )
            )
            rc = (await session.execute(rec_q)).scalars().first()
            if rc:
                recommendations.append(
                    EvidenceItem(
                        id=f"rec-{rc.id}",
                        type="RECOMMENDATION",
                        epistemic_class=EpistemicClass.INFERRED,
                        statement=f"Recommendation '{rc.title}'. Current config: {rc.current_configuration}; Recommended: {rc.recommended_configuration}. Estimated savings: ₹{float(rc.estimated_monthly_savings):,.0f}/month with risk level '{rc.risk_level}'.",
                        value=float(rc.estimated_monthly_savings),
                        unit="INR",
                        source="Atlas Optimizer",
                        source_entity_id=rc.id,
                        confidence=float(rc.confidence_pct) / 100.0 if rc.confidence_pct else 0.85,
                        metadata={
                            "risk_level": rc.risk_level,
                            "category": rc.category,
                            "reasoning": rc.reasoning,
                        },
                    )
                )
                if rc.opportunity and rc.opportunity.resource_id:
                    # Include target resource specs
                    t_res_q = select(CloudResource).where(CloudResource.id == rc.opportunity.resource_id)
                    t_res = (await session.execute(t_res_q)).scalars().first()
                    if t_res:
                        observations.append(
                            EvidenceItem(
                                id=f"res-spec-{t_res.id}",
                                type="RESOURCE_SPEC",
                                epistemic_class=EpistemicClass.OBSERVED,
                                statement=f"Target resource '{t_res.name or t_res.resource_id}' ({t_res.resource_type}), instance type: {t_res.instance_type or 'N/A'}.",
                                source="AWS Resource Inventory",
                                source_entity_id=t_res.id,
                                confidence=1.0,
                            )
                        )

        # 3. SCOPE: SCENARIO
        elif scope_type == ScopeType.SCENARIO and scope_id:
            scen_q = (
                select(Scenario)
                .options(selectinload(Scenario.changes))
                .where(
                    Scenario.id == scope_id,
                    Scenario.org_id == tenant.org_id,
                )
            )
            sc = (await session.execute(scen_q)).scalars().first()
            if sc:
                scenarios.append(
                    EvidenceItem(
                        id=f"scen-{sc.id}",
                        type="SCENARIO",
                        epistemic_class=EpistemicClass.PROJECTED,
                        statement=f"Simulated scenario '{sc.name}' ({sc.scenario_type}). Projected monthly savings: ₹{float(sc.monthly_savings):,.0f} (total changes: {len(sc.changes)}). Note: These are projected savings, not actual historical savings.",
                        value=float(sc.monthly_savings),
                        unit="INR",
                        source="Atlas Scenario Planner",
                        source_entity_id=sc.id,
                        confidence=0.80,
                        metadata={
                            "scenario_type": sc.scenario_type,
                            "changes_count": len(sc.changes),
                        },
                    )
                )

        # 4. SCOPE: DASHBOARD or general
        else:
            # Current vs previous month spend overview
            costs_q = (
                select(
                    CostRecord.usage_date,
                    CostRecord.service_name,
                    func.sum(CostRecord.unblended_cost).label("cost")
                )
                .where(CostRecord.account_id.in_(tenant.account_ids))
                .group_by(CostRecord.usage_date, CostRecord.service_name)
                .order_by(CostRecord.usage_date.desc())
            )
            cost_rows = list((await session.execute(costs_q)).all())

            # Aggregate total by service
            service_totals: Dict[str, float] = {}
            total_spend = 0.0
            for row in cost_rows:
                c = float(row.cost)
                total_spend += c
                service_totals[row.service_name] = service_totals.get(row.service_name, 0.0) + c

            derived_metrics.append(
                EvidenceItem(
                    id="spend-total-aggregate",
                    type="SPEND_TOTAL",
                    epistemic_class=EpistemicClass.DERIVED,
                    statement=f"Total analyzed cloud spend across {len(tenant.account_ids)} accounts is ₹{total_spend:,.0f}.",
                    value=total_spend,
                    unit="INR",
                    source="Atlas Analytics Engine",
                    confidence=1.0,
                )
            )

            # Period Spend Increase / Drivers (from Golden Dataset or DB calculations)
            # In Phase 3 / Golden Scenarios: total spend grew by ₹1.61L with EKS (+₹82K), GPU (+₹51K), S3 (+₹23K)
            # Check if EKS / GPU / S3 have distinct drivers in service_totals
            top_services = sorted(service_totals.items(), key=lambda x: x[1], reverse=True)[:5]
            for s_name, s_val in top_services:
                observations.append(
                    EvidenceItem(
                        id=f"spend-service-{s_name.replace(' ', '-').lower()[:20]}",
                        type="SERVICE_SPEND",
                        epistemic_class=EpistemicClass.OBSERVED,
                        statement=f"Spend for service '{s_name}' is ₹{s_val:,.0f}.",
                        value=s_val,
                        unit="INR",
                        source="Cost Explorer",
                        confidence=1.0,
                        metadata={"service_name": s_name},
                    )
                )

            # Query detected anomalies
            anom_q = (
                select(Anomaly)
                .where(
                    Anomaly.account_id.in_(tenant.account_ids),
                    Anomaly.status == "OPEN",
                )
                .order_by(Anomaly.percentage_change.desc())
                .limit(5)
            )
            anoms = list((await session.execute(anom_q)).scalars().all())
            for an in anoms:
                inferences.append(
                    EvidenceItem(
                        id=f"anom-{an.id}",
                        type="ANOMALY",
                        epistemic_class=EpistemicClass.INFERRED,
                        statement=f"Cost anomaly detected in {an.service_name}: spend jumped +{float(an.percentage_change):.1f}% (observed: ₹{float(an.observed_cost):,.0f} vs baseline: ₹{float(an.baseline_cost):,.0f}). Inferred cause: {an.inferred_cause or 'Under investigation'}.",
                        value=float(an.observed_cost),
                        unit="INR",
                        source="Atlas Anomaly Engine",
                        source_entity_id=an.id,
                        confidence=float(an.confidence_pct) / 100.0 if an.confidence_pct else 0.85,
                        metadata={"service_name": an.service_name, "percentage_change": float(an.percentage_change)},
                    )
                )

            # Query top recommendations
            top_rec_q = (
                select(Recommendation)
                .join(OptimizationOpportunity)
                .where(OptimizationOpportunity.account_id.in_(tenant.account_ids))
                .order_by(Recommendation.estimated_monthly_savings.desc())
                .limit(5)
            )
            top_recs = list((await session.execute(top_rec_q)).scalars().all())
            for tr in top_recs:
                recommendations.append(
                    EvidenceItem(
                        id=f"rec-{tr.id}",
                        type="RECOMMENDATION",
                        epistemic_class=EpistemicClass.INFERRED,
                        statement=f"Recommendation '{tr.title}'. Category: {tr.category}. Estimated savings: ₹{float(tr.estimated_monthly_savings):,.0f}/month.",
                        value=float(tr.estimated_monthly_savings),
                        unit="INR",
                        source="Atlas Optimizer",
                        source_entity_id=tr.id,
                        confidence=float(tr.confidence_pct) / 100.0 if tr.confidence_pct else 0.85,
                    )
                )

        pkg = EvidencePackage(
            scope_type=scope_type,
            scope_id=scope_id,
            freshness=freshness,
            observations=observations,
            derived_metrics=derived_metrics,
            inferences=inferences,
            recommendations=recommendations,
            scenarios=scenarios,
            telemetry=telemetry,
            limitations=limitations,
            evidence_count=len(observations) + len(derived_metrics) + len(inferences) + len(recommendations) + len(scenarios) + len(telemetry),
        )

        return pkg
