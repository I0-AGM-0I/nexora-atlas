"""
NEXORA ATLAS - Phase 6 Spend Concentration Tests
Verifies Top-N shares, descriptive Spend Concentration Index (HHI), and zero-spend handling.
"""

import pytest
from decimal import Decimal

from app.analytics.types import SufficiencyStatus
from app.analytics.drivers.analyzer import CostDriverAnalyzer


def test_spend_concentration_metrics():
    """Verifies Top-N shares and descriptive HHI formula: HHI = sum(share_i^2)."""
    # 3 services: EC2 = 60%, RDS = 30%, S3 = 10%
    # Total spend: 100,000
    services = [
        {"name": "AmazonEC2", "current_cost": Decimal("60000.0000"), "previous_cost": Decimal("50000.0000")},
        {"name": "AmazonRDS", "current_cost": Decimal("30000.0000"), "previous_cost": Decimal("25000.0000")},
        {"name": "AmazonS3", "current_cost": Decimal("10000.0000"), "previous_cost": Decimal("10000.0000")},
    ]
    accounts = [
        {"name": "Production", "current_cost": Decimal("80000.0000"), "previous_cost": Decimal("70000.0000")},
        {"name": "Dev", "current_cost": Decimal("20000.0000"), "previous_cost": Decimal("15000.0000")},
    ]
    resources = [
        {"id": f"res-{i}", "current_cost": Decimal(f"{10000 + i * 2000}.0000")}
        for i in range(6)
    ]

    result = CostDriverAnalyzer.calculate_concentration(services, accounts, resources)

    assert result.sufficiency_status == SufficiencyStatus.AVAILABLE
    # Top 1 service = 60.00%
    assert result.top_1_service_share_pct == Decimal("60.00")
    # Top 3 services = 60 + 30 + 10 = 100.00%
    assert result.top_3_service_share_pct == Decimal("100.00")
    # Top account = 80.00%
    assert result.top_account_share_pct == Decimal("80.00")

    # Descriptive HHI = 60^2 + 30^2 + 10^2 = 3600 + 900 + 100 = 4600.00
    assert result.spend_concentration_index == Decimal("4600.00")
    assert "Highly Concentrated" in result.hhi_interpretation


def test_spend_concentration_zero_spend():
    """Verifies that zero spend safely returns INSUFFICIENT_DATA."""
    result = CostDriverAnalyzer.calculate_concentration([], [], [])
    assert result.sufficiency_status == SufficiencyStatus.INSUFFICIENT_DATA
    assert result.spend_concentration_index == Decimal("0.00")
