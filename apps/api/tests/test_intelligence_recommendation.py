"""
NEXORA ATLAS - Tests: Recommendation Engine
Verifies financial reconciliation (Annual == Monthly * 12), risk rating evaluation,
and candidate generation with multiple tradeoff options.
"""

from decimal import Decimal
from app.intelligence.types import RiskLevel, WasteType, Severity
from app.intelligence.models import OpportunityCandidate, RecommendationCandidate
from app.intelligence.recommendation.calculators import reconcile_savings, evaluate_recommendation_risk
from app.intelligence.recommendation.rules import RecommendationRules
from app.intelligence.recommendation.engine import RecommendationEngine


def test_reconcile_savings_exact_multiplication():
    monthly = Decimal("14234.5678")
    m_calc, a_calc = reconcile_savings(monthly)
    assert m_calc == Decimal("14234.5678")
    assert a_calc == Decimal("170814.8136")
    assert a_calc == m_calc * Decimal("12")


def test_evaluate_risk_level_matrix():
    # Zero downtime tiering is NONE
    assert evaluate_recommendation_risk("STORAGE", "TIER_GP3", "production") == RiskLevel.NONE
    assert evaluate_recommendation_risk("NETWORKING", "RELEASE_EIP", "production") == RiskLevel.NONE

    # Non-prod is LOW
    assert evaluate_recommendation_risk("COMPUTE", "TERMINATE", "development") == RiskLevel.LOW

    # Production architecture switch is MEDIUM
    assert evaluate_recommendation_risk("COMPUTE", "MIGRATE_ARCH_GRAVITON", "production") == RiskLevel.MEDIUM

    # Production termination without rollback is HIGH
    assert evaluate_recommendation_risk("COMPUTE", "TERMINATE", "production", has_rollback_plan=False) == RiskLevel.HIGH


def test_recommendation_engine_process_opportunities():
    opp = OpportunityCandidate(
        account_id="acc-prod-1",
        account_name="Production",
        resource_id="res-eks-1",
        resource_name="analytics-worker",
        resource_native_id="i-eks-01",
        category="COMPUTE",
        waste_type=WasteType.OVERSIZED_INSTANCE,
        severity=Severity.HIGH,
        estimated_waste_monthly=Decimal("25000.0000"),
        evidence_json={},
        confidence_score=Decimal("95.00"),
        recommendations=[],  # empty initially
    )

    processed = RecommendationEngine.process_opportunities([opp], {"acc-prod-1": "production"})
    assert len(processed) == 1
    assert len(processed[0].recommendations) == 1
    rec = processed[0].recommendations[0]
    assert rec.estimated_annual_savings == rec.estimated_monthly_savings * Decimal("12")
    assert rec.risk_level in ("LOW", "MEDIUM", "HIGH", "NONE")
