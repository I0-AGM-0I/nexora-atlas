"""
NEXORA ATLAS - Waste Calculators & Assumption Models
Provides mathematically defensible waste calculations using exact Decimal arithmetic
and explicit, auditable assumptions.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple, Dict, Any
from app.intelligence.constants import (
    DEFAULT_MONTHLY_HOURS,
    BUSINESS_HOURS_PER_MONTH,
    GP2_TO_GP3_PRICE_REDUCTION_RATIO,
)


def calculate_unattached_storage_waste(
    monthly_cost: Decimal,
    days_unattached: int,
) -> Tuple[Decimal, Dict[str, Any]]:
    """
    Unattached storage represents 100% financial waste because the provisioned
    EBS block storage is completely detached from any compute asset.
    """
    waste = monthly_cost.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    assumptions = {
        "waste_factor": "1.00",
        "rationale": "100% of provisioned storage cost is unutilized while detached",
        "days_unattached": days_unattached,
    }
    return waste, assumptions


def calculate_off_hours_idle_waste(
    monthly_cost: Decimal,
    total_hours_per_month: Decimal = DEFAULT_MONTHLY_HOURS,
    business_hours_per_month: Decimal = BUSINESS_HOURS_PER_MONTH,
) -> Tuple[Decimal, Dict[str, Any]]:
    """
    Calculates off-hours waste for non-production environments running 24/7.
    Assumes automated shutdown outside Mon-Fri business hours.
    """
    waste_hours = total_hours_per_month - business_hours_per_month
    waste_ratio = (waste_hours / total_hours_per_month).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    waste = (monthly_cost * waste_ratio).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    assumptions = {
        "operating_schedule": "Monday-Friday 09:00-18:00 IST",
        "total_hours_per_month": str(total_hours_per_month),
        "business_hours_per_month": str(business_hours_per_month),
        "idle_hours_per_month": str(waste_hours),
        "waste_ratio": str(waste_ratio),
    }
    return waste, assumptions


def calculate_gp3_migration_waste(
    monthly_cost: Decimal,
    price_reduction_ratio: Decimal = GP2_TO_GP3_PRICE_REDUCTION_RATIO,
) -> Tuple[Decimal, Dict[str, Any]]:
    """
    Calculates waste attributable to remaining on legacy gp2 storage rather than gp3.
    Explicitly references the 20% standard AWS published pricing differential.
    """
    waste = (monthly_cost * price_reduction_ratio).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    assumptions = {
        "source_tier": "gp2",
        "target_tier": "gp3",
        "pricing_differential_ratio": str(price_reduction_ratio),
        "pricing_source": "AWS standard EBS published storage catalog (gp3 baseline 20% lower than gp2)",
    }
    return waste, assumptions


def calculate_rightsizing_waste(
    current_monthly_cost: Decimal,
    target_monthly_cost: Decimal,
    downsize_ratio: str = "4:1",
) -> Tuple[Decimal, Dict[str, Any]]:
    """
    Calculates compute right-sizing waste based on explicit target tier price.
    """
    waste = max(Decimal("0.0000"), current_monthly_cost - target_monthly_cost).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_UP
    )
    assumptions = {
        "current_monthly_cost": str(current_monthly_cost),
        "target_monthly_cost": str(target_monthly_cost),
        "capacity_downsize_ratio": downsize_ratio,
        "pricing_source": "Deterministic AWS instance catalog benchmark",
    }
    return waste, assumptions
