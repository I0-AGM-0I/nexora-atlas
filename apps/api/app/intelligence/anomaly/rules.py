"""
NEXORA ATLAS - Anomaly Detection Rules with Explicit Evidence Contracts
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple, Optional, Dict, Any
from datetime import date, datetime, timezone
import uuid

from app.intelligence.constants import (
    RULESET_VERSION,
    COST_SPIKE_WARNING_PCT,
    SUSTAINED_INCREASE_MIN_DAYS,
    SUSTAINED_INCREASE_PCT,
    MAD_MIN_POPULATION,
    MAD_OUTLIER_THRESHOLD,
    MAD_ZERO_FALLBACK_SPREAD_PCT,
    ACCOUNT_SHIFT_PCT,
    DEFAULT_BASELINE_WINDOW_DAYS,
)
from app.intelligence.types import AnomalyRuleType, RuleStatus
from app.intelligence.models import EvidenceContract, AnomalyFinding, RuleEvaluationResult
from app.intelligence.baseline.calculator import BaselineCalculator
from app.intelligence.anomaly.scoring import calculate_anomaly_severity, calculate_evidence_strength


class CostSpikeRule:
    """Rule A: Detects sharp single-day cost spikes exceeding historical baseline."""
    rule_id = "ANOM-RULE-A-COST-SPIKE"
    rule_type = AnomalyRuleType.COST_SPIKE
    contract = EvidenceContract(
        rule_name="CostSpikeRule",
        required_fields=["usage_date", "unblended_cost"],
        min_sample_size=4,
        telemetry_source="financial",
    )

    @classmethod
    def evaluate(
        cls,
        account_id: str,
        account_name: str,
        service_name: str,
        series: List[Tuple[date, Decimal]],  # sorted by date asc
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        resource_native_id: Optional[str] = None,
        environment: str = "production",
        run_id: str = "",
    ) -> Tuple[RuleEvaluationResult, Optional[AnomalyFinding]]:
        if not series or len(series) < cls.contract.min_sample_size:
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.rule_type.value,
                    status=RuleStatus.SKIPPED,
                    skip_reason=f"Insufficient cost history (sample_size={len(series)}, required={cls.contract.min_sample_size})",
                    findings_count=0,
                ),
                None,
            )

        sorted_series = sorted(series, key=lambda x: x[0])
        n = len(sorted_series)
        scan_start = max(cls.contract.min_sample_size, n - 30)
        best_finding = None
        highest_pct = Decimal("0.0")

        for idx in range(n - 1, scan_start - 1, -1):
            obs_date, obs_cost = sorted_series[idx]
            historical_series = sorted_series[:idx]
            if len(historical_series) < cls.contract.min_sample_size:
                continue

            baseline_res = BaselineCalculator.calculate(
                historical_series, window_days=DEFAULT_BASELINE_WINDOW_DAYS, algorithm="rolling_mean"
            )
            if not baseline_res.is_sufficient or baseline_res.baseline_value <= Decimal("0.0000"):
                continue

            baseline = baseline_res.baseline_value
            delta = obs_cost - baseline
            pct_change = ((delta / baseline) * Decimal("100.0")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            if delta > Decimal("0.0000") and pct_change >= COST_SPIKE_WARNING_PCT:
                if pct_change > highest_pct:
                    highest_pct = pct_change
                    severity = calculate_anomaly_severity(
                        magnitude_inr=delta,
                        percentage_change=pct_change,
                        duration_days=1,
                        environment=environment,
                    )
                    confidence = calculate_evidence_strength(
                        sample_count=baseline_res.sample_count,
                        window_days=DEFAULT_BASELINE_WINDOW_DAYS,
                        percentage_change=pct_change,
                    )

                    detected_dt = datetime(obs_date.year, obs_date.month, obs_date.day, 12, 0, 0, tzinfo=timezone.utc)
                    best_finding = AnomalyFinding(
                        id=str(uuid.uuid4()),
                        account_id=account_id,
                        account_name=account_name,
                        resource_id=resource_id,
                        resource_name=resource_name,
                        resource_native_id=resource_native_id,
                        service_name=service_name,
                        detected_at=detected_dt,
                        rule_type=cls.rule_type,
                        observed_cost=obs_cost,
                        baseline_cost=baseline,
                        percentage_change=pct_change,
                        severity=severity,
                        confidence_score=confidence,
                        observed_metrics={
                            "observation_date": str(obs_date),
                            "baseline_window_days": DEFAULT_BASELINE_WINDOW_DAYS,
                            "baseline_mean": str(baseline_res.mean_value),
                            "baseline_std_dev": str(baseline_res.std_dev),
                            "delta_cost_inr": str(delta),
                        },
                        inferred_cause=f"Single-day unexpected spending spike of {pct_change}% over historical {DEFAULT_BASELINE_WINDOW_DAYS}-day baseline.",
                        inference_details={
                            "detection_rule": cls.rule_id,
                            "threshold_warning_pct": str(COST_SPIKE_WARNING_PCT),
                            "algorithm": baseline_res.algorithm,
                        },
                        run_id=run_id,
                        ruleset_version=RULESET_VERSION,
                    )

        if best_finding:
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.rule_type.value,
                    status=RuleStatus.EVALUATED_VIOLATION,
                    findings_count=1,
                ),
                best_finding,
            )

        return (
            RuleEvaluationResult(
                rule_id=cls.rule_id,
                rule_type=cls.rule_type.value,
                status=RuleStatus.EVALUATED_CLEAN,
                findings_count=0,
            ),
            None,
        )


class SustainedIncreaseRule:
    """Rule B: Detects cost elevations sustained across multiple consecutive days."""
    rule_id = "ANOM-RULE-B-SUSTAINED-INCREASE"
    rule_type = AnomalyRuleType.SUSTAINED_INCREASE
    contract = EvidenceContract(
        rule_name="SustainedIncreaseRule",
        required_fields=["usage_date", "unblended_cost"],
        min_sample_size=SUSTAINED_INCREASE_MIN_DAYS + 3,
        telemetry_source="financial",
    )

    @classmethod
    def evaluate(
        cls,
        account_id: str,
        account_name: str,
        service_name: str,
        series: List[Tuple[date, Decimal]],
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        resource_native_id: Optional[str] = None,
        environment: str = "production",
        run_id: str = "",
    ) -> Tuple[RuleEvaluationResult, Optional[AnomalyFinding]]:
        if not series or len(series) < cls.contract.min_sample_size:
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.rule_type.value,
                    status=RuleStatus.SKIPPED,
                    skip_reason=f"Insufficient series for sustained analysis (size={len(series)}, required={cls.contract.min_sample_size})",
                    findings_count=0,
                ),
                None,
            )

        sorted_series = sorted(series, key=lambda x: x[0])
        tail_slice = sorted_series[-SUSTAINED_INCREASE_MIN_DAYS:]
        preceding_series = sorted_series[:-SUSTAINED_INCREASE_MIN_DAYS]

        baseline_res = BaselineCalculator.calculate(
            preceding_series, window_days=DEFAULT_BASELINE_WINDOW_DAYS, algorithm="rolling_mean"
        )
        if not baseline_res.is_sufficient or baseline_res.baseline_value <= Decimal("0.0000"):
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.rule_type.value,
                    status=RuleStatus.SKIPPED,
                    skip_reason="Insufficient baseline preceding sustained evaluation window",
                    findings_count=0,
                ),
                None,
            )

        baseline = baseline_res.baseline_value
        all_elevated = True
        consecutive_deltas: List[Decimal] = []

        for d, cost in tail_slice:
            if cost <= baseline:
                all_elevated = False
                break
            pct = ((cost - baseline) / baseline) * Decimal("100.0")
            if pct < SUSTAINED_INCREASE_PCT:
                all_elevated = False
                break
            consecutive_deltas.append(cost - baseline)

        if all_elevated and len(consecutive_deltas) == SUSTAINED_INCREASE_MIN_DAYS:
            mean_observed = sum(x[1] for x in tail_slice) / Decimal(str(len(tail_slice)))
            pct_change = (((mean_observed - baseline) / baseline) * Decimal("100.0")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            severity = calculate_anomaly_severity(
                magnitude_inr=sum(consecutive_deltas),
                percentage_change=pct_change,
                duration_days=SUSTAINED_INCREASE_MIN_DAYS,
                environment=environment,
            )
            confidence = calculate_evidence_strength(
                sample_count=baseline_res.sample_count,
                window_days=DEFAULT_BASELINE_WINDOW_DAYS,
                percentage_change=pct_change,
            )

            latest_date = tail_slice[-1][0]
            detected_dt = datetime(latest_date.year, latest_date.month, latest_date.day, 12, 0, 0, tzinfo=timezone.utc)
            finding = AnomalyFinding(
                id=str(uuid.uuid4()),
                account_id=account_id,
                account_name=account_name,
                resource_id=resource_id,
                resource_name=resource_name,
                resource_native_id=resource_native_id,
                service_name=service_name,
                detected_at=detected_dt,
                rule_type=cls.rule_type,
                observed_cost=mean_observed.quantize(Decimal("0.0001")),
                baseline_cost=baseline,
                percentage_change=pct_change,
                severity=severity,
                confidence_score=confidence,
                observed_metrics={
                    "consecutive_days_elevated": SUSTAINED_INCREASE_MIN_DAYS,
                    "consecutive_dates": [str(x[0]) for x in tail_slice],
                    "mean_daily_observed_cost": str(mean_observed.quantize(Decimal("0.0001"))),
                    "baseline_cost": str(baseline),
                },
                inferred_cause=f"Sustained elevated spending over {SUSTAINED_INCREASE_MIN_DAYS} consecutive days, indicating structural run-rate shift rather than transient spike.",
                inference_details={
                    "detection_rule": cls.rule_id,
                    "sustained_threshold_pct": str(SUSTAINED_INCREASE_PCT),
                },
                run_id=run_id,
                ruleset_version=RULESET_VERSION,
            )
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.rule_type.value,
                    status=RuleStatus.EVALUATED_VIOLATION,
                    findings_count=1,
                ),
                finding,
            )

        return (
            RuleEvaluationResult(
                rule_id=cls.rule_id,
                rule_type=cls.rule_type.value,
                status=RuleStatus.EVALUATED_CLEAN,
                findings_count=0,
            ),
            None,
        )


class ResourceOutlierRule:
    """Rule C: Cross-sectional Median Absolute Deviation (MAD) outlier detector across comparable resources."""
    rule_id = "ANOM-RULE-C-RESOURCE-OUTLIER"
    rule_type = AnomalyRuleType.RESOURCE_OUTLIER
    contract = EvidenceContract(
        rule_name="ResourceOutlierRule",
        required_fields=["resource_id", "period_cost"],
        min_sample_size=MAD_MIN_POPULATION,
        telemetry_source="financial",
    )

    @classmethod
    def evaluate(
        cls,
        account_id: str,
        account_name: str,
        service_name: str,
        resource_items: List[Dict[str, Any]],  # [{resource_id, name, native_id, period_cost: Decimal}]
        environment: str = "production",
        run_id: str = "",
    ) -> Tuple[RuleEvaluationResult, List[AnomalyFinding]]:
        if len(resource_items) < MAD_MIN_POPULATION:
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.rule_type.value,
                    status=RuleStatus.SKIPPED,
                    skip_reason=f"Comparable resource population too small (n={len(resource_items)}, required={MAD_MIN_POPULATION}) for robust MAD outlier detection",
                    findings_count=0,
                ),
                [],
            )

        costs = [item["period_cost"] for item in resource_items]
        median_cost = BaselineCalculator._compute_median(costs)
        mad_val = BaselineCalculator._compute_mad(costs, median_cost)

        findings: List[AnomalyFinding] = []
        now_utc = datetime.now(timezone.utc)

        for item in resource_items:
            c = item["period_cost"]
            is_outlier = False
            pct_deviation = Decimal("0.00")

            if mad_val == Decimal("0.0000"):
                # Handling MAD = 0: When all/most resources have identical cost
                if median_cost > Decimal("0.0000"):
                    pct_deviation = (((c - median_cost) / median_cost) * Decimal("100.0")).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    # Requires material percentage spread AND minimum absolute excess
                    if pct_deviation >= MAD_ZERO_FALLBACK_SPREAD_PCT and (c - median_cost) >= Decimal("1000.0"):
                        is_outlier = True
            else:
                threshold = median_cost + (MAD_OUTLIER_THRESHOLD * mad_val)
                if c > threshold and median_cost > Decimal("0.0000"):
                    is_outlier = True
                    pct_deviation = (((c - median_cost) / median_cost) * Decimal("100.0")).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )

            if is_outlier:
                delta = c - median_cost
                severity = calculate_anomaly_severity(
                    magnitude_inr=delta,
                    percentage_change=pct_deviation,
                    duration_days=30,
                    environment=environment,
                )
                confidence = calculate_evidence_strength(
                    sample_count=len(resource_items),
                    window_days=30,
                    percentage_change=pct_deviation,
                    base_precision=Decimal("88.0"),
                )

                finding = AnomalyFinding(
                    id=str(uuid.uuid4()),
                    account_id=account_id,
                    account_name=account_name,
                    resource_id=item.get("resource_id"),
                    resource_name=item.get("name"),
                    resource_native_id=item.get("native_id"),
                    service_name=service_name,
                    detected_at=now_utc,
                    rule_type=cls.rule_type,
                    observed_cost=c,
                    baseline_cost=median_cost,
                    percentage_change=pct_deviation,
                    severity=severity,
                    confidence_score=confidence,
                    observed_metrics={
                        "cohort_population_size": len(resource_items),
                        "cohort_median_cost": str(median_cost),
                        "cohort_mad": str(mad_val),
                        "mad_threshold_factor": str(MAD_OUTLIER_THRESHOLD),
                        "excess_cost_inr": str(delta),
                    },
                    inferred_cause=f"Resource cost significantly deviates from cohort median across {len(resource_items)} peer resources in {service_name}.",
                    inference_details={
                        "detection_rule": cls.rule_id,
                        "algorithm": "MEDIAN_ABSOLUTE_DEVIATION",
                    },
                    run_id=run_id,
                    ruleset_version=RULESET_VERSION,
                )
                findings.append(finding)

        status = RuleStatus.EVALUATED_VIOLATION if findings else RuleStatus.EVALUATED_CLEAN
        return (
            RuleEvaluationResult(
                rule_id=cls.rule_id,
                rule_type=cls.rule_type.value,
                status=status,
                findings_count=len(findings),
            ),
            findings,
        )


class AccountShiftRule:
    """Rule D: Detects significant proportional shifts in account spend mix."""
    rule_id = "ANOM-RULE-D-ACCOUNT-SHIFT"
    rule_type = AnomalyRuleType.ACCOUNT_SHIFT
    contract = EvidenceContract(
        rule_name="AccountShiftRule",
        required_fields=["account_id", "current_period_spend", "prev_period_spend"],
        min_sample_size=2,
        telemetry_source="financial",
    )

    @classmethod
    def evaluate(
        cls,
        account_id: str,
        account_name: str,
        current_spend: Decimal,
        prev_spend: Decimal,
        org_current_spend: Decimal,
        org_prev_spend: Decimal,
        environment: str = "production",
        run_id: str = "",
    ) -> Tuple[RuleEvaluationResult, Optional[AnomalyFinding]]:
        if prev_spend <= Decimal("0.0000") or org_prev_spend <= Decimal("0.0000"):
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.rule_type.value,
                    status=RuleStatus.SKIPPED,
                    skip_reason="Previous period spend is zero or unavailable for shift comparison",
                    findings_count=0,
                ),
                None,
            )

        pct_change = (((current_spend - prev_spend) / prev_spend) * Decimal("100.0")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        curr_share = (current_spend / org_current_spend) * Decimal("100.0") if org_current_spend > 0 else Decimal("0")
        prev_share = (prev_spend / org_prev_spend) * Decimal("100.0")
        share_delta = (curr_share - prev_share).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Trigger if account grew >= 20% AND gained >= 5% in organizational share
        if pct_change >= ACCOUNT_SHIFT_PCT and share_delta >= Decimal("5.0"):
            delta_cost = current_spend - prev_spend
            severity = calculate_anomaly_severity(
                magnitude_inr=delta_cost,
                percentage_change=pct_change,
                duration_days=30,
                environment=environment,
            )
            confidence = calculate_evidence_strength(
                sample_count=30,
                window_days=30,
                percentage_change=pct_change,
                base_precision=Decimal("92.0"),
            )
            now_utc = datetime.now(timezone.utc)

            finding = AnomalyFinding(
                id=str(uuid.uuid4()),
                account_id=account_id,
                account_name=account_name,
                resource_id=None,
                resource_name=None,
                resource_native_id=None,
                service_name="CloudAccount",
                detected_at=now_utc,
                rule_type=cls.rule_type,
                observed_cost=current_spend,
                baseline_cost=prev_spend,
                percentage_change=pct_change,
                severity=severity,
                confidence_score=confidence,
                observed_metrics={
                    "current_period_spend": str(current_spend),
                    "previous_period_spend": str(prev_spend),
                    "current_org_share_pct": str(curr_share.quantize(Decimal("0.01"))),
                    "previous_org_share_pct": str(prev_share.quantize(Decimal("0.01"))),
                    "share_expansion_pct": str(share_delta),
                },
                inferred_cause=f"Account spend expanded by {pct_change}% (+{share_delta}% share of overall organization spend), driving macroeconomic cost growth.",
                inference_details={
                    "detection_rule": cls.rule_id,
                    "account_shift_threshold_pct": str(ACCOUNT_SHIFT_PCT),
                },
                run_id=run_id,
                ruleset_version=RULESET_VERSION,
            )
            return (
                RuleEvaluationResult(
                    rule_id=cls.rule_id,
                    rule_type=cls.rule_type.value,
                    status=RuleStatus.EVALUATED_VIOLATION,
                    findings_count=1,
                ),
                finding,
            )

        return (
            RuleEvaluationResult(
                rule_id=cls.rule_id,
                rule_type=cls.rule_type.value,
                status=RuleStatus.EVALUATED_CLEAN,
                findings_count=0,
            ),
            None,
        )
