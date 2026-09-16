"""
NEXORA ATLAS - Demo Engine Configuration
Fixed seed and synthetic baseline parameters.
"""

from datetime import date, timedelta
from decimal import Decimal

DEMO_SEED = 424242

# Organization Identity
DEMO_ORG_NAME = "Nexora Labs Inc"
DEMO_ORG_SLUG = "nexora-labs"
DEMO_CURRENCY = "INR"
DEMO_TIMEZONE = "Asia/Kolkata"

# Synthetic Accounts
DEMO_ACCOUNTS = [
    {
        "account_id": "111222333444",
        "name": "Production Core",
        "provider_type": "AWS",
        "env": "production",
        "target_share": 0.74,
    },
    {
        "account_id": "222333444555",
        "name": "Staging Workloads",
        "provider_type": "AWS",
        "env": "staging",
        "target_share": 0.12,
    },
    {
        "account_id": "333444555666",
        "name": "Development Sandbox",
        "provider_type": "AWS",
        "env": "development",
        "target_share": 0.14,
    },
]

# Cloud Regions
DEMO_REGIONS = [
    {"region_code": "ap-south-1", "display_name": "Asia Pacific (Mumbai)", "provider_type": "AWS"},
    {"region_code": "us-east-1", "display_name": "US East (N. Virginia)", "provider_type": "AWS"},
    {"region_code": "us-west-2", "display_name": "US West (Oregon)", "provider_type": "AWS"},
    {"region_code": "eu-west-1", "display_name": "Europe (Ireland)", "provider_type": "AWS"},
]

# Timeframe: 90 days ending yesterday (for complete days)
REFERENCE_END_DATE = date(2026, 9, 15)
HISTORY_DAYS = 90
REFERENCE_START_DATE = REFERENCE_END_DATE - timedelta(days=HISTORY_DAYS - 1)

# Monthly target run rate: ~₹21.4 Lakhs
TARGET_MONTHLY_SPEND = Decimal("2140000.0000")
TARGET_POTENTIAL_SAVINGS = Decimal("460000.0000")
