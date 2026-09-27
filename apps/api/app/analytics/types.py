"""
NEXORA ATLAS - Advanced Analytics Domain Types & Enums
"""

from enum import Enum


class DataCategory(str, Enum):
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    INFERRED = "INFERRED"
    ASSUMED = "ASSUMED"
    PROJECTED = "PROJECTED"


class SufficiencyStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class TrendDirection(str, Enum):
    INCREASING = "INCREASING"
    DECREASING = "DECREASING"
    STABLE = "STABLE"
    VOLATILE = "VOLATILE"


class CostRegime(str, Enum):
    SPIKE = "SPIKE"
    RECOVERY = "RECOVERY"
    ELEVATED = "ELEVATED"
    NORMAL = "NORMAL"


class DriverDimension(str, Enum):
    SERVICE = "SERVICE"
    ACCOUNT = "ACCOUNT"
    RESOURCE = "RESOURCE"
    REGION = "REGION"


class ChangeClassification(str, Enum):
    USAGE = "USAGE"
    LIKELY_USAGE_DRIVEN = "LIKELY_USAGE_DRIVEN"
    PRICE_CONFIG = "PRICE_CONFIG"
    MIX_SHIFT = "MIX_SHIFT"
    NEW_RESOURCE = "NEW_RESOURCE"
    REMOVED_RESOURCE = "REMOVED_RESOURCE"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class DependencyType(str, Enum):
    REQUIRED_DEPENDENCY = "REQUIRED_DEPENDENCY"
    RECOMMENDED_PRECAUTION = "RECOMMENDED_PRECAUTION"


class ComplexityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ReversibilityLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ScenarioType(str, Enum):
    CONSERVATIVE = "CONSERVATIVE"
    AGGRESSIVE = "AGGRESSIVE"
    MODERNIZATION = "MODERNIZATION"
    CUSTOM = "CUSTOM"
