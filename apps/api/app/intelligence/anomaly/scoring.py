"""
NEXORA ATLAS - Anomaly Scoring & Evidence Strength Models
Computes context-aware severity (incorporating environment, duration, and magnitude)
and deterministic evidence-strength confidence scores.
"""

from decimal import Decimal, ROUND_HALF_UP
from app.intelligence.types import Severity


def calculate_anomaly_severity(
    magnitude_inr: Decimal,
    percentage_change: Decimal,
    duration_days: int = 1,
    environment: str = "production",
) -> Severity:
    """
    Computes deterministic context-aware severity.
    Unlike naive billing thresholding, incorporates:
    - Absolute financial magnitude in INR
    - Percentage deviation
    - Duration of the deviation (single-day vs sustained)
    - Workload environment context (Production carries higher priority than Development)
    """
    env_lower = environment.lower()
    is_prod = "prod" in env_lower
    is_dev = "dev" in env_lower or "sandbox" in env_lower

    # Compute a contextual composite severity score
    # Baseline weight from percentage change
    if percentage_change >= Decimal("50.0"):
        pct_score = 40
    elif percentage_change >= Decimal("30.0"):
        pct_score = 25
    elif percentage_change >= Decimal("20.0"):
        pct_score = 15
    else:
        pct_score = 5

    # Financial magnitude weight (INR)
    abs_mag = abs(magnitude_inr)
    if abs_mag >= Decimal("100000.0"):      # >= 1 Lakh
        mag_score = 40
    elif abs_mag >= Decimal("30000.0"):     # >= 30k
        mag_score = 25
    elif abs_mag >= Decimal("10000.0"):     # >= 10k
        mag_score = 15
    elif abs_mag >= Decimal("2000.0"):      # >= 2k
        mag_score = 10
    else:
        mag_score = 5

    # Duration bonus
    duration_score = 15 if duration_days >= 3 else 5

    # Environment multiplier
    if is_prod:
        env_multiplier = Decimal("1.3")
    elif is_dev:
        env_multiplier = Decimal("0.8")
    else:
        env_multiplier = Decimal("1.0")

    total_score = Decimal(str(pct_score + mag_score + duration_score)) * env_multiplier

    if total_score >= Decimal("90.0"):
        return Severity.CRITICAL
    elif total_score >= Decimal("65.0"):
        return Severity.HIGH
    elif total_score >= Decimal("40.0"):
        return Severity.MEDIUM
    elif total_score >= Decimal("20.0"):
        return Severity.LOW
    else:
        return Severity.INFO


def calculate_evidence_strength(
    sample_count: int,
    window_days: int,
    percentage_change: Decimal,
    base_precision: Decimal = Decimal("85.0"),
) -> Decimal:
    """
    Computes deterministic evidence strength (0-100%).
    Confidence represents deterministic evidence strength under the current ruleset;
    it is NOT a statistical probability of correctness.

    Derived from:
    - Sample observation completeness (actual vs requested window)
    - Signal-to-noise strength (magnitude of percentage change)
    """
    completeness_ratio = min(Decimal("1.0"), Decimal(str(sample_count)) / Decimal(str(max(1, window_days))))
    sample_factor = completeness_ratio * Decimal("10.0")

    if abs(percentage_change) >= Decimal("50.0"):
        signal_factor = Decimal("5.0")
    elif abs(percentage_change) >= Decimal("25.0"):
        signal_factor = Decimal("3.0")
    else:
        signal_factor = Decimal("1.0")

    raw_strength = base_precision + sample_factor + signal_factor
    clamped = min(Decimal("99.00"), max(Decimal("50.00"), raw_strength))
    return clamped.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
