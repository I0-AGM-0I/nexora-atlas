"""
NEXORA ATLAS - Forecast Fixtures Generator
Creates forward-looking statistical trajectory fixtures.
Marked explicitly with algorithm="demo_fixture" (zero fake AI claim).
"""

from decimal import Decimal
from datetime import date
from typing import List, Dict, Any


def generate_forecasts(account_map: Dict[str, str]) -> List[Dict[str, Any]]:
    prod_acc_id = account_map["111222333444"]

    drivers = [
        {"service": "AmazonEC2", "driver_weight": 0.42, "growth_driver": "Compute auto-scaling & web traffic"},
        {"service": "GPU_AI_Workloads", "driver_weight": 0.28, "growth_driver": "Expanded model inference volume"},
        {"service": "AmazonRDS", "driver_weight": 0.18, "growth_driver": "Database read IOPS & storage expansion"},
        {"service": "AmazonS3", "driver_weight": 0.12, "growth_driver": "Data lake raw telemetry ingestion"},
    ]

    forecasts = [
        {
            "account_id": prod_acc_id,
            "forecast_month": date(2026, 10, 1),
            "projected_cost": Decimal("2380000.0000"),
            "lower_bound": Decimal("2240000.0000"),
            "upper_bound": Decimal("2520000.0000"),
            "confidence_pct": Decimal("88.00"),
            "cost_drivers_json": drivers,
            "algorithm": "demo_fixture",
        },
        {
            "account_id": prod_acc_id,
            "forecast_month": date(2026, 11, 1),
            "projected_cost": Decimal("2650000.0000"),
            "lower_bound": Decimal("2480000.0000"),
            "upper_bound": Decimal("2820000.0000"),
            "confidence_pct": Decimal("85.00"),
            "cost_drivers_json": drivers,
            "algorithm": "demo_fixture",
        },
        {
            "account_id": prod_acc_id,
            "forecast_month": date(2026, 12, 1),
            "projected_cost": Decimal("3140000.0000"),
            "lower_bound": Decimal("2910000.0000"),
            "upper_bound": Decimal("3370000.0000"),
            "confidence_pct": Decimal("82.00"),
            "cost_drivers_json": drivers,
            "algorithm": "demo_fixture",
        },
    ]

    return forecasts
