"""
NEXORA ATLAS - Intelligence Engine Orchestrator
Coordinates the complete intelligence pipeline: Baselines -> Anomalies -> Waste -> Recommendations -> Idempotent Persistence.
"""

import uuid
from decimal import Decimal
from datetime import datetime, timezone, date, timedelta
from typing import Optional, List, Dict, Tuple, Any
from collections import defaultdict

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.intelligence.constants import RULESET_VERSION
from app.intelligence.models import (
    IntelligenceRunResult,
    AnomalyFinding,
    OpportunityCandidate,
    RuleEvaluationResult,
)
from app.intelligence.anomaly.detector import AnomalyDetector
from app.intelligence.waste.detector import WasteDetector
from app.intelligence.recommendation.engine import RecommendationEngine

from app.models.account import CloudAccount
from app.models.resource import CloudResource, Tag
from app.models.cost import CostRecord
from app.models.anomaly import Anomaly
from app.models.optimization import OptimizationOpportunity, Recommendation
from app.models.organization import AuditLog
from app.models.telemetry import ResourceMetricObservation


class IntelligenceEngine:
    """Production intelligence coordinator enforcing zero-mutation analysis and idempotent persistence."""

    @classmethod
    async def run(
        cls,
        db: AsyncSession,
        organization_id: str,
        run_id: Optional[str] = None,
    ) -> IntelligenceRunResult:
        started_at = datetime.now(timezone.utc)
        resolved_run_id = run_id or f"intel-run-{uuid.uuid4().hex[:12]}"

        # 1. Fetch Cloud Accounts for Organization
        acc_stmt = select(CloudAccount).where(CloudAccount.org_id == organization_id)
        accounts_db = (await db.execute(acc_stmt)).scalars().all()
        if not accounts_db:
            # Clean exit if organization has no connected accounts
            completed_at = datetime.now(timezone.utc)
            return IntelligenceRunResult(
                run_id=resolved_run_id,
                organization_id=organization_id,
                ruleset_version=RULESET_VERSION,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=int((completed_at - started_at).total_seconds() * 1000),
                anomalies_detected=0,
                opportunities_found=0,
                recommendations_generated=0,
                potential_monthly_savings=Decimal("0.0000"),
                potential_annual_savings=Decimal("0.0000"),
                rule_evaluations=[],
                anomalies=[],
                opportunities=[],
            )

        account_ids = [acc.id for acc in accounts_db]
        accounts_payload: List[Dict[str, Any]] = [
            {"id": acc.id, "name": acc.name, "account_id": acc.account_id}
            for acc in accounts_db
        ]
        environment_by_account: Dict[str, str] = {
            acc.id: "production" if "prod" in acc.name.lower() else ("development" if "dev" in acc.name.lower() else "staging")
            for acc in accounts_db
        }

        # 2. Fetch Resources and Tags
        res_stmt = (
            select(CloudResource)
            .options(selectinload(CloudResource.tags))
            .where(CloudResource.account_id.in_(account_ids))
        )
        resources_db = (await db.execute(res_stmt)).scalars().all()

        # Fetch recent 14-day operational telemetry observations
        now_utc = datetime.now(timezone.utc)
        telemetry_start = now_utc - timedelta(days=14)
        obs_stmt = (
            select(ResourceMetricObservation)
            .where(
                ResourceMetricObservation.resource_id.in_([r.id for r in resources_db]),
                ResourceMetricObservation.timestamp >= telemetry_start,
            )
            .order_by(ResourceMetricObservation.timestamp.asc())
        )
        obs_rows = (await db.execute(obs_stmt)).scalars().all()

        obs_by_res_and_metric: Dict[Tuple[str, str], List[ResourceMetricObservation]] = defaultdict(list)
        for obs in obs_rows:
            obs_by_res_and_metric[(obs.resource_id, obs.metric_name)].append(obs)

        resources_payload: List[Dict[str, Any]] = []
        for r in resources_db:
            env = environment_by_account.get(r.account_id, "production")
            for t in r.tags:
                if t.key.lower() == "environment":
                    env = t.value.lower()
                    break

            specs = dict(r.specs_json or {})

            # Enrich from canonical CloudWatch telemetry if observations exist
            cpu_obs = obs_by_res_and_metric.get((r.id, "CPUUtilization"), [])
            if cpu_obs:
                from app.integrations.providers.aws.telemetry.processor import TelemetryStatisticalProcessor
                cpu_stats = TelemetryStatisticalProcessor.process_observations(
                    metric_name="CPUUtilization",
                    unit="Percent",
                    observations=cpu_obs,
                    window_start=telemetry_start,
                    window_end=now_utc,
                )
                if cpu_stats.p95 is not None:
                    specs["p95_cpu_utilization_pct"] = str(cpu_stats.p95)
                    specs["cpu_utilization_p95"] = float(cpu_stats.p95)
                    specs["telemetry_coverage_ratio"] = str(cpu_stats.coverage_ratio)
                    specs["telemetry_sample_count"] = cpu_stats.sample_count
                    specs["telemetry_sufficiency"] = cpu_stats.sufficiency_status.value
                    specs["telemetry_mean_cpu"] = str(cpu_stats.mean)

            conn_obs = obs_by_res_and_metric.get((r.id, "DatabaseConnections"), [])
            if conn_obs:
                from app.integrations.providers.aws.telemetry.processor import TelemetryStatisticalProcessor
                conn_stats = TelemetryStatisticalProcessor.process_observations(
                    metric_name="DatabaseConnections",
                    unit="Count",
                    observations=conn_obs,
                    window_start=telemetry_start,
                    window_end=now_utc,
                    is_activity_metric=True,
                )
                if conn_stats.maximum is not None:
                    specs["active_client_connections"] = int(conn_stats.maximum)
                    specs["avg_connections"] = int(conn_stats.mean or 0)

            resources_payload.append({
                "id": r.id,
                "account_id": r.account_id,
                "service_name": r.service_name,
                "resource_type": r.resource_type,
                "native_id": r.native_id,
                "name": r.name,
                "status": r.status,
                "specs_json": specs,
                "environment": env,
            })

        # 3. Fetch Cost Records & Build Telemetry Time-Series
        cost_stmt = (
            select(CostRecord)
            .where(CostRecord.account_id.in_(account_ids))
            .order_by(CostRecord.usage_date.asc())
        )
        records = (await db.execute(cost_stmt)).scalars().all()

        daily_by_resource: Dict[Tuple[str, date], Decimal] = defaultdict(Decimal)
        daily_by_account: Dict[Tuple[str, date], Decimal] = defaultdict(Decimal)
        all_dates = set()

        for rec in records:
            all_dates.add(rec.usage_date)
            daily_by_account[(rec.account_id, rec.usage_date)] += rec.unblended_cost
            if rec.resource_id:
                daily_by_resource[(rec.resource_id, rec.usage_date)] += rec.unblended_cost

        max_date = max(all_dates) if all_dates else date.today()
        cutoff_30d = max_date - timedelta(days=30)
        cutoff_60d = max_date - timedelta(days=60)

        # Build sorted series for anomaly analysis
        cost_series_by_resource: Dict[str, List[Tuple[date, Decimal]]] = {}
        monthly_costs_by_resource: Dict[str, Decimal] = defaultdict(Decimal)

        # Pre-group daily points
        points_by_res: Dict[str, Dict[date, Decimal]] = defaultdict(dict)
        for (r_id, d), amt in daily_by_resource.items():
            points_by_res[r_id][d] = amt
            if d > cutoff_30d:
                monthly_costs_by_resource[r_id] += amt

        for r_id, d_map in points_by_res.items():
            sorted_series = sorted(d_map.items(), key=lambda x: x[0])
            cost_series_by_resource[r_id] = sorted_series

        account_spends_current_30d: Dict[str, Decimal] = defaultdict(Decimal)
        account_spends_prev_30d: Dict[str, Decimal] = defaultdict(Decimal)

        for (acc_id, d), amt in daily_by_account.items():
            if d > cutoff_30d:
                account_spends_current_30d[acc_id] += amt
            elif cutoff_60d < d <= cutoff_30d:
                account_spends_prev_30d[acc_id] += amt

        # 4. Run Anomaly Detector (Rules A, B, C, D)
        anomalies, anomaly_evals = AnomalyDetector.detect(
            accounts=accounts_payload,
            resources=resources_payload,
            cost_series_by_resource=cost_series_by_resource,
            account_spends_current_30d=account_spends_current_30d,
            account_spends_prev_30d=account_spends_prev_30d,
            run_id=resolved_run_id,
        )

        # 5. Run Waste Detector (Rules 1 - 7 with Evidence Contracts)
        opportunities, waste_evals = WasteDetector.detect(
            accounts=accounts_payload,
            resources=resources_payload,
            monthly_costs_by_resource=monthly_costs_by_resource,
            run_id=resolved_run_id,
        )

        # 6. Run Recommendation Engine (Tradeoff Options & Reconciliation)
        opportunities = RecommendationEngine.process_opportunities(
            opportunities=opportunities,
            environment_by_account=environment_by_account,
        )

        # 7. Idempotent Database Upsert
        # A. Upsert Anomalies
        existing_anomalies_stmt = (
            select(Anomaly)
            .where(
                and_(
                    Anomaly.account_id.in_(account_ids),
                    Anomaly.status == "OPEN",
                )
            )
        )
        existing_anomalies = (await db.execute(existing_anomalies_stmt)).scalars().all()
        anomaly_lookup = {
            (a.account_id, a.resource_id, a.detection_rule): a
            for a in existing_anomalies
        }

        for finding in anomalies:
            rule_key = finding.anomaly_type.value
            key = (finding.account_id, finding.resource_id, rule_key)

            if key in anomaly_lookup:
                # Update existing open anomaly
                existing = anomaly_lookup[key]
                existing.observed_cost = finding.detected_spend
                existing.baseline_cost = finding.expected_spend
                existing.percentage_change = finding.percentage_deviation
                existing.severity = finding.severity.value
                existing.inferred_cause = finding.evidence_json.get("inferred_cause") or f"{finding.anomaly_type.value} detected"
                existing.confidence_pct = Decimal(str(finding.evidence_json.get("confidence_score", "90.00")))
                existing.observed_metrics_json = finding.evidence_json.get("observed_facts", {})
                existing.inference_details_json = finding.evidence_json.get("inferences", {})
                existing.detected_at = datetime.now(timezone.utc)
            else:
                new_anomaly = Anomaly(
                    account_id=finding.account_id,
                    resource_id=finding.resource_id,
                    service_name=finding.service_name,
                    observed_cost=finding.detected_spend,
                    baseline_cost=finding.expected_spend,
                    percentage_change=finding.percentage_deviation,
                    detected_at=datetime.now(timezone.utc),
                    detection_rule=rule_key,
                    observed_metrics_json=finding.evidence_json.get("observed_facts", {}),
                    severity=finding.severity.value,
                    status="OPEN",
                    inferred_cause=finding.evidence_json.get("inferred_cause") or f"{finding.anomaly_type.value} detected",
                    confidence_pct=Decimal(str(finding.evidence_json.get("confidence_score", "90.00"))),
                    inference_details_json=finding.evidence_json.get("inferences", {}),
                )
                db.add(new_anomaly)

        # B. Upsert Optimization Opportunities & Recommendations
        existing_opps_stmt = (
            select(OptimizationOpportunity)
            .options(selectinload(OptimizationOpportunity.recommendations))
            .where(
                and_(
                    OptimizationOpportunity.account_id.in_(account_ids),
                    OptimizationOpportunity.status == "OPEN",
                )
            )
        )
        existing_opps = (await db.execute(existing_opps_stmt)).scalars().all()
        opp_lookup = {
            (o.account_id, o.resource_id, o.waste_type): o
            for o in existing_opps
        }

        total_recs_count = 0
        for opp in opportunities:
            opp_key = (opp.account_id, opp.resource_id, opp.waste_type.value)
            total_recs_count += len(opp.recommendations)

            if opp_key in opp_lookup:
                # Update existing opportunity
                existing_opp = opp_lookup[opp_key]
                existing_opp.estimated_waste_monthly = opp.estimated_waste_monthly
                existing_opp.severity = opp.severity.value
                existing_opp.evidence_json = opp.evidence_json

                # Match recommendations under this opportunity
                existing_recs_map = {r.title: r for r in existing_opp.recommendations}
                for rec_cand in opp.recommendations:
                    if rec_cand.title in existing_recs_map:
                        rec_db = existing_recs_map[rec_cand.title]
                        rec_db.current_configuration = rec_cand.current_configuration
                        rec_db.recommended_configuration = rec_cand.recommended_configuration
                        rec_db.estimated_monthly_savings = rec_cand.estimated_monthly_savings
                        rec_db.estimated_annual_savings = rec_cand.estimated_annual_savings
                        rec_db.confidence_pct = rec_cand.confidence_score
                        rec_db.risk_level = rec_cand.risk_level
                        rec_db.reasoning = rec_cand.reasoning
                        rec_db.evidence_json = rec_cand.evidence_json
                    else:
                        new_rec = Recommendation(
                            opportunity_id=existing_opp.id,
                            resource_id=opp.resource_id,
                            category=rec_cand.category,
                            title=rec_cand.title,
                            current_configuration=rec_cand.current_configuration,
                            recommended_configuration=rec_cand.recommended_configuration,
                            estimated_monthly_savings=rec_cand.estimated_monthly_savings,
                            estimated_annual_savings=rec_cand.estimated_annual_savings,
                            confidence_pct=rec_cand.confidence_score,
                            risk_level=rec_cand.risk_level,
                            reasoning=rec_cand.reasoning,
                            evidence_json=rec_cand.evidence_json,
                            status="OPEN",
                        )
                        db.add(new_rec)
            else:
                new_opp = OptimizationOpportunity(
                    account_id=opp.account_id,
                    resource_id=opp.resource_id,
                    category=opp.category,
                    waste_type=opp.waste_type.value,
                    severity=opp.severity.value,
                    status="OPEN",
                    estimated_waste_monthly=opp.estimated_waste_monthly,
                    evidence_json=opp.evidence_json,
                )
                db.add(new_opp)
                await db.flush()  # Obtain new_opp.id

                for rec_cand in opp.recommendations:
                    new_rec = Recommendation(
                        opportunity_id=new_opp.id,
                        resource_id=opp.resource_id,
                        category=rec_cand.category,
                        title=rec_cand.title,
                        current_configuration=rec_cand.current_configuration,
                        recommended_configuration=rec_cand.recommended_configuration,
                        estimated_monthly_savings=rec_cand.estimated_monthly_savings,
                        estimated_annual_savings=rec_cand.estimated_annual_savings,
                        confidence_pct=rec_cand.confidence_score,
                        risk_level=rec_cand.risk_level,
                        reasoning=rec_cand.reasoning,
                        evidence_json=rec_cand.evidence_json,
                        status="OPEN",
                    )
                    db.add(new_rec)

        # 8. Record Immutable Audit Log Entry
        potential_monthly_savings = sum((o.estimated_waste_monthly for o in opportunities), Decimal("0.0000")).quantize(Decimal("0.0001"))
        potential_annual_savings = (potential_monthly_savings * Decimal("12")).quantize(Decimal("0.0001"))
        completed_at = datetime.now(timezone.utc)
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        audit_entry = AuditLog(
            org_id=organization_id,
            actor_id="system:atlas-intelligence-engine",
            action="INTELLIGENCE_ANALYSIS_EXECUTED",
            entity_type="INTELLIGENCE_RUN",
            entity_id=resolved_run_id,
            metadata_json={
                "run_id": resolved_run_id,
                "ruleset_version": RULESET_VERSION,
                "duration_ms": duration_ms,
                "anomalies_detected": len(anomalies),
                "opportunities_found": len(opportunities),
                "recommendations_generated": total_recs_count,
                "potential_monthly_savings_inr": str(potential_monthly_savings),
                "potential_annual_savings_inr": str(potential_annual_savings),
            },
        )
        db.add(audit_entry)
        await db.commit()

        return IntelligenceRunResult(
            run_id=resolved_run_id,
            organization_id=organization_id,
            ruleset_version=RULESET_VERSION,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            anomalies_detected=len(anomalies),
            opportunities_found=len(opportunities),
            recommendations_generated=total_recs_count,
            potential_monthly_savings=potential_monthly_savings,
            potential_annual_savings=potential_annual_savings,
            rule_evaluations=anomaly_evals + waste_evals,
            anomalies=anomalies,
            opportunities=opportunities,
        )

    @classmethod
    async def get_status(
        cls,
        db: AsyncSession,
        organization_id: str,
    ) -> Dict[str, Any]:
        """Returns the operational status, active findings count, and audit info of the engine."""
        # Query latest audit log
        audit_stmt = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.org_id == organization_id,
                    AuditLog.action == "INTELLIGENCE_ANALYSIS_EXECUTED",
                )
            )
            .order_by(AuditLog.timestamp.desc())
            .limit(1)
        )
        latest_audit = (await db.execute(audit_stmt)).scalar_one_or_none()

        # Query active counts
        acc_stmt = select(CloudAccount.id).where(CloudAccount.org_id == organization_id)
        account_ids = (await db.execute(acc_stmt)).scalars().all()

        anomaly_count = 0
        opp_count = 0
        monthly_savings = Decimal("0.0000")

        if account_ids:
            anom_stmt = select(Anomaly).where(
                and_(Anomaly.account_id.in_(account_ids), Anomaly.status == "OPEN")
            )
            active_anomalies = (await db.execute(anom_stmt)).scalars().all()
            anomaly_count = len(active_anomalies)

            opp_stmt = select(OptimizationOpportunity).where(
                and_(OptimizationOpportunity.account_id.in_(account_ids), OptimizationOpportunity.status == "OPEN")
            )
            active_opps = (await db.execute(opp_stmt)).scalars().all()
            opp_count = len(active_opps)
            monthly_savings = sum((o.estimated_waste_monthly for o in active_opps), Decimal("0.0000"))

        annual_savings = (monthly_savings * Decimal("12")).quantize(Decimal("0.0001"))

        return {
            "ruleset_version": RULESET_VERSION,
            "status": "READY",
            "last_run_at": latest_audit.timestamp.isoformat() if latest_audit else None,
            "last_run_id": latest_audit.entity_id if latest_audit else None,
            "active_anomalies_count": anomaly_count,
            "active_opportunities_count": opp_count,
            "addressable_monthly_savings": monthly_savings,
            "addressable_annual_savings": annual_savings,
            "is_offline_mode": True,
            "aws_network_disabled": True,
        }
