"""
NEXORA ATLAS - Anomaly Detection Engine
Coordinates evidence verification, statistical baselines, and rule execution.
"""

from decimal import Decimal
from typing import List, Dict, Tuple, Any, Optional
from datetime import date

from app.intelligence.models import AnomalyFinding, RuleEvaluationResult
from app.intelligence.anomaly.rules import (
    CostSpikeRule,
    SustainedIncreaseRule,
    ResourceOutlierRule,
    AccountShiftRule,
)


class AnomalyDetector:
    """Orchestrates deterministic anomaly detection across accounts and resources."""

    @classmethod
    def detect(
        cls,
        accounts: List[Dict[str, Any]],  # [{id, name, ...}]
        resources: List[Dict[str, Any]], # [{id, account_id, name, native_id, service_name, resource_type, environment, ...}]
        cost_series_by_resource: Dict[str, List[Tuple[date, Decimal]]],
        account_spends_current_30d: Dict[str, Decimal],
        account_spends_prev_30d: Dict[str, Decimal],
        run_id: str = "",
    ) -> Tuple[List[AnomalyFinding], List[RuleEvaluationResult]]:
        findings: List[AnomalyFinding] = []
        eval_results: List[RuleEvaluationResult] = []

        account_map = {acc["id"]: acc["name"] for acc in accounts}

        # 1. Rule A: Cost Spikes & Rule B: Sustained Increases on Resource Series
        spike_evals: List[RuleEvaluationResult] = []
        sustained_evals: List[RuleEvaluationResult] = []

        for res in resources:
            r_id = res["id"]
            series = cost_series_by_resource.get(r_id, [])
            acc_id = res["account_id"]
            acc_name = account_map.get(acc_id, "Unknown Account")
            env = res.get("environment", "production")

            # Evaluate Rule A
            res_spike_eval, spike_finding = CostSpikeRule.evaluate(
                account_id=acc_id,
                account_name=acc_name,
                service_name=res["service_name"],
                series=series,
                resource_id=r_id,
                resource_name=res.get("name"),
                resource_native_id=res.get("native_id"),
                environment=env,
                run_id=run_id,
            )
            spike_evals.append(res_spike_eval)
            if spike_finding:
                findings.append(spike_finding)

            # Evaluate Rule B
            res_sust_eval, sustained_finding = SustainedIncreaseRule.evaluate(
                account_id=acc_id,
                account_name=acc_name,
                service_name=res["service_name"],
                series=series,
                resource_id=r_id,
                resource_name=res.get("name"),
                resource_native_id=res.get("native_id"),
                environment=env,
                run_id=run_id,
            )
            sustained_evals.append(res_sust_eval)
            if sustained_finding:
                findings.append(sustained_finding)

        # Aggregate Rule A & B evaluation results for clean run summary
        spike_violations = sum(1 for e in spike_evals if e.status.value == "EVALUATED_VIOLATION")
        spike_skips = sum(1 for e in spike_evals if e.status.value == "SKIPPED")
        eval_results.append(
            RuleEvaluationResult(
                rule_id=CostSpikeRule.rule_id,
                rule_type=CostSpikeRule.rule_type.value,
                status="EVALUATED_VIOLATION" if spike_violations > 0 else "EVALUATED_CLEAN",
                skip_reason=f"{spike_skips} resources skipped due to insufficient history" if spike_skips > 0 else None,
                findings_count=spike_violations,
            )
        )

        sust_violations = sum(1 for e in sustained_evals if e.status.value == "EVALUATED_VIOLATION")
        sust_skips = sum(1 for e in sustained_evals if e.status.value == "SKIPPED")
        eval_results.append(
            RuleEvaluationResult(
                rule_id=SustainedIncreaseRule.rule_id,
                rule_type=SustainedIncreaseRule.rule_type.value,
                status="EVALUATED_VIOLATION" if sust_violations > 0 else "EVALUATED_CLEAN",
                skip_reason=f"{sust_skips} resources skipped due to insufficient history" if sust_skips > 0 else None,
                findings_count=sust_violations,
            )
        )

        # 2. Rule C: Resource Outlier Detection (Cross-sectional by service/resource_type)
        # Group resources by (account_id, service_name, resource_type)
        grouped_resources: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = {}
        for res in resources:
            r_id = res["id"]
            series = cost_series_by_resource.get(r_id, [])
            # Calculate 30d spend for cross-sectional comparison
            period_cost = sum(x[1] for x in series[-30:]) if series else Decimal("0.0000")
            key = (res["account_id"], res["service_name"], res["resource_type"])
            if key not in grouped_resources:
                grouped_resources[key] = []
            grouped_resources[key].append({
                "resource_id": r_id,
                "name": res.get("name"),
                "native_id": res.get("native_id"),
                "period_cost": period_cost,
                "environment": res.get("environment", "production"),
            })

        outlier_violations = 0
        outlier_skips = 0
        for (acc_id, s_name, r_type), cohort in grouped_resources.items():
            acc_name = account_map.get(acc_id, "Unknown Account")
            env = cohort[0]["environment"] if cohort else "production"
            outlier_eval, cohort_findings = ResourceOutlierRule.evaluate(
                account_id=acc_id,
                account_name=acc_name,
                service_name=s_name,
                resource_items=cohort,
                environment=env,
                run_id=run_id,
            )
            if outlier_eval.status.value == "SKIPPED":
                outlier_skips += 1
            elif outlier_eval.status.value == "EVALUATED_VIOLATION":
                outlier_violations += len(cohort_findings)
                findings.extend(cohort_findings)

        eval_results.append(
            RuleEvaluationResult(
                rule_id=ResourceOutlierRule.rule_id,
                rule_type=ResourceOutlierRule.rule_type.value,
                status="EVALUATED_VIOLATION" if outlier_violations > 0 else ("SKIPPED" if outlier_skips == len(grouped_resources) else "EVALUATED_CLEAN"),
                skip_reason=f"{outlier_skips} cohorts had insufficient population (n < {ResourceOutlierRule.contract.min_sample_size})" if outlier_skips > 0 else None,
                findings_count=outlier_violations,
            )
        )

        # 3. Rule D: Account Shift Detection
        org_current = sum(account_spends_current_30d.values())
        org_prev = sum(account_spends_prev_30d.values())
        shift_violations = 0

        for acc in accounts:
            a_id = acc["id"]
            a_name = acc["name"]
            curr_val = account_spends_current_30d.get(a_id, Decimal("0.0000"))
            prev_val = account_spends_prev_30d.get(a_id, Decimal("0.0000"))
            shift_eval, shift_finding = AccountShiftRule.evaluate(
                account_id=a_id,
                account_name=a_name,
                current_spend=curr_val,
                prev_spend=prev_val,
                org_current_spend=org_current,
                org_prev_spend=org_prev,
                environment="production" if "prod" in a_name.lower() else "staging",
                run_id=run_id,
            )
            if shift_finding:
                shift_violations += 1
                findings.append(shift_finding)

        eval_results.append(
            RuleEvaluationResult(
                rule_id=AccountShiftRule.rule_id,
                rule_type=AccountShiftRule.rule_type.value,
                status="EVALUATED_VIOLATION" if shift_violations > 0 else "EVALUATED_CLEAN",
                findings_count=shift_violations,
            )
        )

        return findings, eval_results
