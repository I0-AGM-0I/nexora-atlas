"""
NEXORA ATLAS - Waste Detection Orchestrator
Iterates resources across accounts and executes waste rules with contract verification.
"""

from decimal import Decimal
from typing import List, Dict, Tuple, Any, Optional

from app.intelligence.types import WasteType, Severity, RuleStatus
from app.intelligence.models import OpportunityCandidate, RuleEvaluationResult
from app.intelligence.waste.rules import (
    UnattachedVolumeRule,
    OversizedInstanceRule,
    OffHoursIdleRule,
    IdleDatabaseRule,
    LegacyStorageTierRule,
    UnassociatedEIPRule,
    UnmanagedObjectVersionsRule,
)


class WasteDetector:
    """Orchestrates deterministic waste and inefficiency detection across cloud resources."""

    RULES = [
        UnattachedVolumeRule,
        OversizedInstanceRule,
        OffHoursIdleRule,
        IdleDatabaseRule,
        LegacyStorageTierRule,
        UnassociatedEIPRule,
        UnmanagedObjectVersionsRule,
    ]

    @classmethod
    def detect(
        cls,
        accounts: List[Dict[str, Any]],
        resources: List[Dict[str, Any]],
        monthly_costs_by_resource: Dict[str, Decimal],
        run_id: str = "",
    ) -> Tuple[List[OpportunityCandidate], List[RuleEvaluationResult]]:
        opportunities: List[OpportunityCandidate] = []
        eval_results: List[RuleEvaluationResult] = []
        account_map = {acc["id"]: acc.get("name", "Unknown Account") for acc in accounts}

        for rule_cls in cls.RULES:
            rule_violations: List[OpportunityCandidate] = []
            skipped_count = 0
            clean_count = 0
            skip_reasons = set()

            for res in resources:
                r_id = res["id"]
                monthly_cost = monthly_costs_by_resource.get(r_id, Decimal("0.0000"))
                acc_name = account_map.get(res["account_id"], "Unknown Account")

                eval_res, opp = rule_cls.evaluate(
                    resource=res,
                    monthly_cost=monthly_cost,
                    account_name=acc_name,
                    run_id=run_id,
                )

                if eval_res.status == RuleStatus.SKIPPED:
                    skipped_count += 1
                    if eval_res.skip_reason:
                        skip_reasons.add(eval_res.skip_reason)
                elif eval_res.status == RuleStatus.EVALUATED_VIOLATION:
                    if opp:
                        rule_violations.append(opp)
                        opportunities.append(opp)
                elif eval_res.status == RuleStatus.EVALUATED_CLEAN:
                    clean_count += 1

            # Compile top-level rule evaluation result
            if len(rule_violations) > 0:
                overall_status = RuleStatus.EVALUATED_VIOLATION
                skip_msg = f"{skipped_count} resources skipped" if skipped_count > 0 else None
            elif clean_count > 0:
                overall_status = RuleStatus.EVALUATED_CLEAN
                skip_msg = f"{skipped_count} resources skipped" if skipped_count > 0 else None
            else:
                overall_status = RuleStatus.SKIPPED
                skip_msg = f"All {skipped_count} resources skipped ({'; '.join(sorted(skip_reasons))[:100]})"

            eval_results.append(
                RuleEvaluationResult(
                    rule_id=rule_cls.rule_id,
                    rule_type=rule_cls.waste_type.value,
                    status=overall_status,
                    skip_reason=skip_msg,
                    findings_count=len(rule_violations),
                )
            )

        return opportunities, eval_results
