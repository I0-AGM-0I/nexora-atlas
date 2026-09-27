"""
NEXORA ATLAS - Optimization Prioritization & Trade-off Assessment
Evaluates independent dimensions (Impact, Confidence, Risk, Complexity, Reversibility) without black-box scores.
"""

from decimal import Decimal
from typing import Dict, Any, Tuple

from app.analytics.types import ComplexityLevel, ReversibilityLevel


def assess_recommendation_tradeoffs(
    category: str,
    action_type: str,
    risk_level: str,
    estimated_monthly_savings: Decimal,
    confidence_score: Decimal,
) -> Dict[str, Any]:
    """
    Evaluates transparent, independent decision dimensions for an optimization opportunity:
    1. Financial Impact (Monthly Savings in INR)
    2. Confidence (Evidence Strength %)
    3. Operational Risk (LOW / MEDIUM / HIGH)
    4. Implementation Complexity (LOW / MEDIUM / HIGH)
    5. Reversibility (HIGH / MEDIUM / LOW)

    STRICT BOUNDARY: Does NOT compute a composite 'magic score' or choose for the user.
    """
    action_upper = action_type.upper()
    cat_upper = category.upper()

    # Complexity assessment
    if "MIGRATION" in action_upper or "MODERNIZATION" in action_upper or "GRAVITON" in action_upper:
        complexity = ComplexityLevel.HIGH
    elif "DOWNSIZE" in action_upper or "RIGHTSIZE" in action_upper:
        complexity = ComplexityLevel.MEDIUM
    else:  # e.g. delete unattached EBS, release unassociated EIP, stop idle instance
        complexity = ComplexityLevel.LOW

    # Reversibility assessment
    if "DELETE" in action_upper or "TERMINATE" in action_upper:
        reversibility = ReversibilityLevel.LOW
    elif "MIGRATION" in action_upper or "ARCHITECTURE" in action_upper:
        reversibility = ReversibilityLevel.MEDIUM
    else:  # Resize, stop/start, tag
        reversibility = ReversibilityLevel.HIGH

    return {
        "financial_impact_monthly": estimated_monthly_savings,
        "confidence_pct": confidence_score,
        "risk_level": risk_level.upper(),
        "complexity_level": complexity.value,
        "reversibility_level": reversibility.value,
    }
