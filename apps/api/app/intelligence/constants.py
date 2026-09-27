"""
NEXORA ATLAS - Intelligence Engine Constants & Thresholds
Centralizes all statistical parameters, detection thresholds, and ruleset versioning.
"""

from decimal import Decimal

# Ruleset Versioning & Provenance
RULESET_VERSION = "atlas-intelligence-v1"

# Baseline Calculation
DEFAULT_BASELINE_WINDOW_DAYS = 14
SHORT_BASELINE_WINDOW_DAYS = 7
LONG_BASELINE_WINDOW_DAYS = 30
MIN_BASELINE_SAMPLES = 3

# Anomaly Detection Thresholds
COST_SPIKE_WARNING_PCT = Decimal("20.0")
COST_SPIKE_CRITICAL_PCT = Decimal("50.0")

SUSTAINED_INCREASE_MIN_DAYS = 3
SUSTAINED_INCREASE_PCT = Decimal("15.0")

MAD_MIN_POPULATION = 4
MAD_OUTLIER_THRESHOLD = Decimal("2.5")
MAD_ZERO_FALLBACK_SPREAD_PCT = Decimal("25.0")

ACCOUNT_SHIFT_PCT = Decimal("20.0")

# Waste Detection Thresholds
IDLE_CPU_THRESHOLD_PCT = Decimal("10.0")
IDLE_MEMORY_THRESHOLD_PCT = Decimal("20.0")

OVERSIZED_CPU_THRESHOLD_PCT = Decimal("30.0")
OVERSIZED_MEMORY_THRESHOLD_PCT = Decimal("40.0")

UNATTACHED_STORAGE_MIN_DAYS = 7

IDLE_DB_MAX_CONNECTIONS = 1
IDLE_DB_MIN_DAYS = 14

UNASSOCIATED_EIP_MIN_DAYS = 7

# Operational Telemetry Thresholds
MIN_TELEMETRY_COVERAGE_FOR_RIGHTSIZING = Decimal("0.70")
HIGH_MEMORY_CONSTRAINED_THRESHOLD_PCT = Decimal("80.0")

# Recommendation & Pricing Assumptions
DEFAULT_MONTHLY_HOURS = Decimal("720")
BUSINESS_HOURS_PER_MONTH = Decimal("180")  # Mon-Fri 09:00-18:00 IST (approx 9h * 20d)
GP2_TO_GP3_PRICE_REDUCTION_RATIO = Decimal("0.20")  # 20% standard AWS storage price difference
