"""
NEXORA ATLAS - Deterministic Cost Record & Snapshot Generator
Synthesizes 90 days of daily financial line items with day-of-week modulation,
growth trajectories, and intentional controlled events.
"""

import random
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Tuple, Any
from app.demo.config import DEMO_SEED, REFERENCE_START_DATE, HISTORY_DAYS


def quantize_money(amount: float) -> Decimal:
    """Safely convert float calculation to 4-decimal Decimal."""
    return Decimal(str(round(amount, 4))).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def generate_cost_history(
    resources: List[Dict[str, Any]],
    account_map: Dict[str, str],   # maps account_id string -> account DB uuid
    resource_map: Dict[str, str],  # maps native_id -> resource DB uuid
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generates deterministic daily CostRecord and aggregate CostSnapshot entries.
    Uses seeded pseudo-randomness for 100% reproducible numerical output.
    """
    rng = random.Random(DEMO_SEED)
    cost_records: List[Dict[str, Any]] = []

    # Map of (account_id, period_start, period_type) -> {total, breakdown}
    daily_aggregates: Dict[Tuple[str, date], Dict[str, Any]] = {}
    monthly_aggregates: Dict[Tuple[str, date, date], Dict[str, Any]] = {}

    for day_idx in range(HISTORY_DAYS):
        current_date = REFERENCE_START_DATE + timedelta(days=day_idx)
        dow = current_date.weekday()  # 0 = Monday, 6 = Sunday

        for res in resources:
            raw_acc_id = res["account_id"]
            acc_db_id = account_map[raw_acc_id]
            native_id = res["native_id"]
            res_db_id = resource_map[native_id]
            service_name = res["service_name"]
            base_cost = res["base_daily_cost"]

            # 1. Base jitter (±2%)
            jitter = rng.uniform(0.98, 1.02)
            daily_cost = base_cost * jitter

            # 2. Day-of-week modulation
            if "staging" in res["tags"].get("Environment", "") or "development" in res["tags"].get("Environment", ""):
                if dow in [5, 6]:
                    # Dev environments slightly drop on weekends, but waste resources stay high
                    if res["resource_type"] == "Instance" and "dev-sandbox" in native_id:
                        daily_cost *= 0.85  # stays ~85% active even on weekends (waste rule evidence!)
                    else:
                        daily_cost *= 0.50

            # 3. Intentional Event 1: S3 Data Accumulation (steady linear growth over 90 days)
            if service_name == "AmazonS3":
                growth_factor = 1.0 + (day_idx / HISTORY_DAYS) * 0.24  # +24% growth
                daily_cost *= growth_factor

            # 4. Intentional Event 2: AI GPU Inference Surge (Days 65 to 90)
            if "g4dn" in native_id and day_idx >= 65:
                daily_cost *= 1.52  # +52% spike

            # 5. Intentional Event 3: Production Core API Workload Spike (Days 75 to 85)
            if "prod-api-worker" in native_id and 75 <= day_idx <= 85:
                daily_cost *= 1.38  # +38% spike

            # 6. Intentional Event 4: Staging Data Transfer Surge (Days 80 to 83)
            if "staging-api" in native_id and 80 <= day_idx <= 83:
                daily_cost *= 1.45

            decimal_cost = quantize_money(daily_cost)

            # Determine usage unit and quantity
            if res["resource_type"] == "Instance":
                quantity = Decimal("24.0000")
                unit = "Hrs"
            elif res["resource_type"] == "Volume":
                quantity = Decimal(str(res["specs_json"].get("size_gb", 100)))
                unit = "GB-Mo"
            elif res["resource_type"] == "Bucket":
                quantity = Decimal(str(res["specs_json"].get("approx_size_tb", 1.0)))
                unit = "TB-Mo"
            else:
                quantity = Decimal("1.0000")
                unit = "Count"

            cost_records.append({
                "account_id": acc_db_id,
                "resource_id": res_db_id,
                "service_name": service_name,
                "usage_date": current_date,
                "unblended_cost": decimal_cost,
                "amortized_cost": decimal_cost,
                "usage_quantity": quantity,
                "usage_unit": unit,
                "currency": "INR",
            })

            # Track daily aggregation
            daily_key = (acc_db_id, current_date)
            if daily_key not in daily_aggregates:
                daily_aggregates[daily_key] = {"total": Decimal("0.0000"), "breakdown": {}}
            daily_aggregates[daily_key]["total"] += decimal_cost
            breakdown = daily_aggregates[daily_key]["breakdown"]
            breakdown[service_name] = breakdown.get(service_name, Decimal("0.0000")) + decimal_cost

            # Track monthly aggregation (bucket by month start)
            month_start = date(current_date.year, current_date.month, 1)
            # month end is first day of next month minus 1
            if current_date.month == 12:
                month_end = date(current_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(current_date.year, current_date.month + 1, 1) - timedelta(days=1)

            monthly_key = (acc_db_id, month_start, month_end)
            if monthly_key not in monthly_aggregates:
                monthly_aggregates[monthly_key] = {"total": Decimal("0.0000"), "breakdown": {}}
            monthly_aggregates[monthly_key]["total"] += decimal_cost
            m_breakdown = monthly_aggregates[monthly_key]["breakdown"]
            m_breakdown[service_name] = m_breakdown.get(service_name, Decimal("0.0000")) + decimal_cost

    # Convert aggregates into CostSnapshot dictionaries
    snapshots: List[Dict[str, Any]] = []

    # Monthly snapshots
    for (acc_db_id, m_start, m_end), data in monthly_aggregates.items():
        # JSON serialize breakdown decimals to floats for API compatibility
        json_breakdown = {k: float(v) for k, v in data["breakdown"].items()}
        snapshots.append({
            "account_id": acc_db_id,
            "period_start": m_start,
            "period_end": m_end,
            "period_type": "MONTHLY",
            "total_cost": data["total"],
            "breakdown_json": json_breakdown,
        })

    # Daily snapshots (for recent 30 days)
    recent_30_start = REFERENCE_START_DATE + timedelta(days=60)
    for (acc_db_id, day_date), data in daily_aggregates.items():
        if day_date >= recent_30_start:
            json_breakdown = {k: float(v) for k, v in data["breakdown"].items()}
            snapshots.append({
                "account_id": acc_db_id,
                "period_start": day_date,
                "period_end": day_date,
                "period_type": "DAILY",
                "total_cost": data["total"],
                "breakdown_json": json_breakdown,
            })

    return cost_records, snapshots
