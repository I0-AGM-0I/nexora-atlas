"""
NEXORA ATLAS - Advanced Analytics Constants & Thresholds
Centralizes all statistical parameters, analytical windows, regime bands, and versioning.
"""

from decimal import Decimal

# Versioning & Provenance
ANALYTICS_VERSION = "atlas-analytics-v1"
SCENARIO_VERSION = "atlas-scenarios-v1"
PRICING_BASIS_SYNTHETIC = "synthetic_demo"

# Analysis Windows
WINDOW_7D = 7
WINDOW_14D = 14
WINDOW_30D = 30
DEFAULT_COMPARISON_WINDOW_DAYS = 30
MIN_TREND_SAMPLES = 3

# Trend Classification Thresholds
# Precedence: CV >= CV_VOLATILE_THRESHOLD -> VOLATILE
# otherwise delta > +3% -> INCREASING
# otherwise delta < -3% -> DECREASING
# otherwise -> STABLE
STABLE_DELTA_PCT = Decimal("3.0")
CV_VOLATILE_THRESHOLD = Decimal("0.25")

# Regime Classification Thresholds
# Precedence: SPIKE -> RECOVERY -> ELEVATED -> NORMAL
REGIME_NORMAL_BAND_PCT = Decimal("10.0")
REGIME_ELEVATED_PCT = Decimal("10.0")
REGIME_ELEVATED_MIN_DAYS = 3
REGIME_SPIKE_PCT = Decimal("50.0")

# Efficiency & Headroom
HEADROOM_SUSTAINED_DAYS = 14
PERCENTILE_P95 = Decimal("95.0")

# Scenarios & Assumptions
DEFAULT_MONTHLY_HOURS = Decimal("720")
BUSINESS_HOURS_PER_MONTH = Decimal("180")
DAYS_PER_MONTH = 30
