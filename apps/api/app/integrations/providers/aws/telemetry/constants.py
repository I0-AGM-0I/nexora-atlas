"""
NEXORA ATLAS - Telemetry Constants & Thresholds
Defines versioning, pagination limits, coverage thresholds, and retention policies.
"""

from decimal import Decimal

# Telemetry catalog version
TELEMETRY_CATALOG_VERSION = "atlas-telemetry-v1"

# Ingestion windows and resolutions
DEFAULT_TELEMETRY_WINDOW_DAYS = 14
EXTENDED_TELEMETRY_WINDOW_DAYS = 30
DEFAULT_METRIC_PERIOD_SECONDS = 3600  # 1 hour standard resolution
DETAILED_METRIC_PERIOD_SECONDS = 300  # 5 minutes detailed resolution

# Safety and performance ceilings (Guardrails against runaway ingestion)
MAX_PAGES_PER_QUERY = 10
MAX_DATA_POINTS_PER_SYNC = 50_000
MAX_RESOURCES_PER_TELEMETRY_SYNC = 200
MAX_METRIC_DATA_QUERIES_PER_REQUEST = 500  # AWS hard limit on MetricDataQuery items in GetMetricData

# Analytical thresholds
MIN_TELEMETRY_COVERAGE_FOR_RIGHTSIZING = Decimal("0.70")  # Minimum 70% coverage required
MIN_TELEMETRY_SAMPLES_FOR_ANALYSIS = 24  # Minimum 24 hourly samples
MAX_ACCEPTABLE_FRESHNESS_AGE_HOURS = 48  # Data older than 48 hours is considered stale

# Retention policy
DEFAULT_RAW_TELEMETRY_RETENTION_DAYS = 30
