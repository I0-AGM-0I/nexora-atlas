"""
NEXORA ATLAS - Recommendation Financial Calculators and Risk Scorers
Guarantees mathematical reconciliation: Monthly * 12 = Annual, pure Decimal.
"""

from decimal import Decimal
from typing import Tuple, Dict, Any
from app.intelligence.types import RiskLevel


def reconcile_savings(monthly: Decimal) -> Tuple[Decimal, Decimal]:
    """
    Computes and quantizes monthly and annual savings in INR.
    Guarantees exact mathematical reconciliation: annual == monthly * 12.
    """
    quantized_monthly = monthly.quantize(Decimal("0.0001"))
    quantized_annual = (quantized_monthly * Decimal("12")).quantize(Decimal("0.0001"))
    return quantized_monthly, quantized_annual


def evaluate_recommendation_risk(
    category: str,
    action_type: str,
    environment: str = "production",
    has_rollback_plan: bool = True,
) -> RiskLevel:
    """
    Deterministically determines risk level based on operational blast radius.
    """
    env_lower = environment.lower()
    action_upper = action_type.upper()

    # 1. Non-production or zero-downtime tiering
    if "RELEASE_EIP" in action_upper or "TIER_GP3" in action_upper:
        return RiskLevel.NONE

    if env_lower in ("development", "dev", "sandbox"):
        return RiskLevel.LOW

    # 2. Production changes
    if "MIGRATE_ARCH" in action_upper or "GRAVITON" in action_upper:
        return RiskLevel.MEDIUM

    if "TERMINATE" in action_upper or "DELETE" in action_upper:
        return RiskLevel.MEDIUM if has_rollback_plan else RiskLevel.HIGH

    if "DOWNSIZE" in action_upper:
        return RiskLevel.LOW if has_rollback_plan else RiskLevel.MEDIUM

    return RiskLevel.LOW
