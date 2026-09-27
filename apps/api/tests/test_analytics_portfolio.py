"""
NEXORA ATLAS - Phase 6 Optimization Portfolio Tests
Verifies conflict detection, dependency mapping, descriptive risk, and compatible savings aggregation.
"""

import pytest
from decimal import Decimal

from app.analytics.types import DependencyType
from app.analytics.optimization.prioritization import assess_recommendation_tradeoffs
from app.analytics.optimization.portfolio import OptimizationPortfolio


def test_independent_tradeoffs_no_magic_score():
    """Verifies that trade-offs are evaluated across 5 transparent dimensions without a magic score."""
    tradeoffs = assess_recommendation_tradeoffs(
        category="RIGHTSIZING",
        action_type="Downsize Compute Instance",
        risk_level="MEDIUM",
        estimated_monthly_savings=Decimal("15000.0000"),
        confidence_score=Decimal("92.50"),
    )
    # 5 independent dimensions
    assert tradeoffs["financial_impact_monthly"] == Decimal("15000.0000")
    assert tradeoffs["confidence_pct"] == Decimal("92.50")
    assert tradeoffs["risk_level"] == "MEDIUM"
    assert tradeoffs["complexity_level"] == "MEDIUM"
    assert tradeoffs["reversibility_level"] == "HIGH"
    # Zero composite score
    assert "score" not in tradeoffs
    assert "magic_score" not in tradeoffs


def test_portfolio_conflict_detection_and_compatible_aggregation():
    """
    Verifies Correction 8, 9 & 28:
    - Multiple recommendations targeting the same resource are flagged as conflicts.
    - Resolves a non-conflicting compatible portfolio without double-counting.
    - Portfolio risk profile is descriptive (zero composite score).
    """
    opportunities = [
        {"id": "opp-1", "resource_id": "res-ec2-1", "estimated_waste_monthly": Decimal("25000.0000")},
        {"id": "opp-2", "resource_id": "res-ebs-1", "estimated_waste_monthly": Decimal("5000.0000")},
    ]

    recommendations = [
        # Option A on res-ec2-1: In-family downsize (saves 15,000)
        {
            "id": "rec-1a",
            "resource_id": "res-ec2-1",
            "title": "Downsize m5.2xlarge to m5.large",
            "category": "RIGHTSIZING",
            "current_configuration": "m5.2xlarge",
            "recommended_configuration": "m5.large",
            "estimated_monthly_savings": Decimal("15000.0000"),
            "risk_level": "LOW",
        },
        # Option B on res-ec2-1: Graviton Modernization (saves 20,000) -> CONFLICTS WITH OPTION A!
        {
            "id": "rec-1b",
            "resource_id": "res-ec2-1",
            "title": "Migrate to c7g.xlarge Graviton",
            "category": "RIGHTSIZING",
            "current_configuration": "m5.2xlarge",
            "recommended_configuration": "c7g.xlarge",
            "estimated_monthly_savings": Decimal("20000.0000"),
            "risk_level": "MEDIUM",
        },
        # Recommendation on res-ebs-1: Delete unattached volume (saves 5,000)
        {
            "id": "rec-2",
            "resource_id": "res-ebs-1",
            "title": "Delete Unattached EBS Volume",
            "category": "UNATTACHED_VOLUME",
            "current_configuration": "gp2 500GB",
            "recommended_configuration": "None",
            "estimated_monthly_savings": Decimal("5000.0000"),
            "risk_level": "LOW",
        },
    ]

    portfolio = OptimizationPortfolio.evaluate(opportunities, recommendations)

    # 1. Conflict detection: res-ec2-1 has conflicting options
    assert len(portfolio.conflicts) == 1
    assert portfolio.conflicts[0].resource_id == "res-ec2-1"
    assert set(portfolio.conflicts[0].recommendation_ids) == {"rec-1a", "rec-1b"}

    # 2. Compatible aggregation: only 1 option for res-ec2-1 is counted (rec-1a: 15000 + rec-2: 5000 = 20000)
    # Zero double-counting of 15000 + 20000
    assert portfolio.compatible_recommendations_count == 2
    assert portfolio.total_compatible_monthly_savings == Decimal("20000.0000")
    assert portfolio.total_compatible_annual_savings == Decimal("240000.0000")

    # 3. Descriptive risk profile (Correction 9)
    assert portfolio.risk_profile.highest_risk == "LOW"
    assert portfolio.risk_profile.count_low == 2
    assert portfolio.risk_profile.count_medium == 0
    assert portfolio.risk_profile.count_high == 0

    # 4. Dependencies (Correction 10)
    # rec-1b (Graviton) declared REQUIRED_DEPENDENCY; rec-2 (EBS) declared RECOMMENDED_PRECAUTION
    dep_types = [d.dependency_type for d in portfolio.dependencies]
    assert DependencyType.REQUIRED_DEPENDENCY in dep_types
    assert DependencyType.RECOMMENDED_PRECAUTION in dep_types
