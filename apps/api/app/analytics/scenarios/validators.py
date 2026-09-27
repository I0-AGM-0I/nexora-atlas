"""
NEXORA ATLAS - Scenario Constraint Validators
Enforces architectural safety rules and financial invariants for simulated scenarios.
"""

from decimal import Decimal
from typing import List, Dict, Any, Optional

from app.analytics.models import ScenarioConstraintViolation


def validate_scenario_change(
    change_type: str,
    resource: Optional[Dict[str, Any]] = None,
    proposed_spec: Optional[str] = None,
) -> List[ScenarioConstraintViolation]:
    """
    Validates architectural constraints for a proposed change:
    - Production workloads cannot be scheduled for off-hours shutdown.
    - High-availability database replicas cannot be terminated.
    - ARM Graviton migration requires ARM-compatible software stack.
    """
    violations: List[ScenarioConstraintViolation] = []
    if not resource:
        return violations

    res_id = str(resource.get("id", ""))
    res_name = str(resource.get("name", "")).lower()
    tags = resource.get("tags") or {}
    env = str(tags.get("Environment", tags.get("env", ""))).lower()
    is_prod = env == "production" or "prod" in res_name

    # 1. No Off-Hours Shutdown on Production
    if change_type.upper() in ("OFF_HOURS_SHUTDOWN", "SCHEDULE_STOP"):
        if is_prod:
            violations.append(
                ScenarioConstraintViolation(
                    rule_name="NO_PROD_OFF_HOURS_SHUTDOWN",
                    resource_id=res_id,
                    reason=f"Production resource '{resource.get('name')}' cannot be scheduled for off-hours shutdown.",
                    severity="ERROR",
                )
            )

    # 2. Preserve High-Availability DB Replicas
    if change_type.upper() in ("TERMINATE_REPLICA", "REMOVE_STANDBY"):
        service = str(resource.get("service_name", ""))
        specs = resource.get("specs_json") or {}
        is_ha = specs.get("multi_az", False) or "replica" in res_name or "standby" in res_name
        if service == "AmazonRDS" and is_ha:
            violations.append(
                ScenarioConstraintViolation(
                    rule_name="PRESERVE_HA_DATABASE_REPLICA",
                    resource_id=res_id,
                    reason=f"High-availability database replica '{resource.get('name')}' cannot be terminated.",
                    severity="ERROR",
                )
            )

    # 3. ARM Migration Compatibility
    if change_type.upper() in ("ARM_MIGRATION", "GRAVITON_UPGRADE"):
        specs = resource.get("specs_json") or {}
        arch = specs.get("architecture", "x86_64")
        if specs.get("legacy_x86_locked", False):
            violations.append(
                ScenarioConstraintViolation(
                    rule_name="ARM_COMPATIBILITY_REQUIRED",
                    resource_id=res_id,
                    reason=f"Resource '{resource.get('name')}' has legacy x86 locked binaries incompatible with Graviton.",
                    severity="ERROR",
                )
            )

    return violations


def validate_scenario_financials(
    baseline_monthly_cost: Decimal,
    projected_monthly_cost: Decimal,
    monthly_savings: Decimal,
    annual_savings: Decimal,
    change_deltas: List[Decimal],
) -> List[ScenarioConstraintViolation]:
    """
    Validates strict Decimal financial invariants:
    1. baseline - projected == monthly_savings
    2. monthly_savings * 12 == annual_savings
    3. sum(change_deltas) == -monthly_savings
    """
    violations: List[ScenarioConstraintViolation] = []

    # Invariant 1: baseline - projected == monthly_savings
    expected_savings = baseline_monthly_cost - projected_monthly_cost
    if expected_savings != monthly_savings:
        violations.append(
            ScenarioConstraintViolation(
                rule_name="FINANCIAL_INVARIANT_MONTHLY_SAVINGS",
                reason=f"Monthly savings ({monthly_savings}) != baseline ({baseline_monthly_cost}) - projected ({projected_monthly_cost})",
                severity="ERROR",
            )
        )

    # Invariant 2: monthly_savings * 12 == annual_savings
    expected_annual = monthly_savings * Decimal("12")
    if expected_annual != annual_savings:
        violations.append(
            ScenarioConstraintViolation(
                rule_name="FINANCIAL_INVARIANT_ANNUAL_SAVINGS",
                reason=f"Annual savings ({annual_savings}) != monthly_savings ({monthly_savings}) * 12",
                severity="ERROR",
            )
        )

    # Invariant 3: sum(change_deltas) == -monthly_savings
    total_delta = sum(change_deltas, Decimal("0.0000"))
    if total_delta != -monthly_savings:
        violations.append(
            ScenarioConstraintViolation(
                rule_name="FINANCIAL_INVARIANT_DELTA_SUM",
                reason=f"Sum of change deltas ({total_delta}) != -monthly_savings ({-monthly_savings})",
                severity="ERROR",
            )
        )

    return violations
