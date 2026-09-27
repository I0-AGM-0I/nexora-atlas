"""
NEXORA ATLAS - AI Domain Types & Enums (Phase 9)
Defines epistemic classes, question categories, scopes, and error taxonomies.
"""

from enum import Enum


class EpistemicClass(str, Enum):
    """
    Epistemic boundary classification.
    Strictly preserves the distinction between observed facts and modeled outcomes.
    """
    OBSERVED = "OBSERVED"          # Direct factual observation (e.g. AWS Cost Explorer line item, exact instance type)
    DERIVED = "DERIVED"            # Deterministic mathematical calculation (e.g. daily average spend, p95 metric)
    INFERRED = "INFERRED"          # Rule-based conclusion based on evidence (e.g. idle database via connection count)
    ASSUMED = "ASSUMED"            # Default parameter or assumption (e.g. 50% target utilization, 730 hrs/month)
    PROJECTED = "PROJECTED"        # Modeled future or hypothetical outcome (e.g. scenario savings, forecast)
    NOT_AVAILABLE = "NOT_AVAILABLE"# Insufficient or missing data


class QuestionCategory(str, Enum):
    """Deterministic question category for evidence retrieval planning."""
    SPEND_OVERVIEW = "SPEND_OVERVIEW"
    SPEND_CHANGE = "SPEND_CHANGE"
    COST_DRIVER = "COST_DRIVER"
    ANOMALY = "ANOMALY"
    OPTIMIZATION = "OPTIMIZATION"
    RESOURCE = "RESOURCE"
    TELEMETRY = "TELEMETRY"
    SCENARIO = "SCENARIO"
    FORECAST = "FORECAST"
    ACCOUNT = "ACCOUNT"
    SERVICE = "SERVICE"
    GENERAL_ATLAS = "GENERAL_ATLAS"
    UNSUPPORTED = "UNSUPPORTED"


class ScopeType(str, Enum):
    """Controlled scope boundary for query execution."""
    DASHBOARD = "DASHBOARD"          # Organization-wide overview
    SERVICE = "SERVICE"              # Specific cloud service
    ACCOUNT = "ACCOUNT"              # Specific cloud account
    RESOURCE = "RESOURCE"            # Specific resource ID
    RECOMMENDATION = "RECOMMENDATION"# Specific optimization recommendation
    SCENARIO = "SCENARIO"            # Specific what-if scenario


class AIResponseStatus(str, Enum):
    """Lifecycle status of an AI explanation query."""
    COMPLETED = "COMPLETED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    DISABLED = "DISABLED"
    RATE_LIMITED = "RATE_LIMITED"


class ProviderErrorCode(str, Enum):
    """Explicit taxonomy of AI provider errors."""
    TIMEOUT = "TIMEOUT"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    RATE_LIMIT = "RATE_LIMIT"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    UNKNOWN = "UNKNOWN"


class DataFreshnessStatus(str, Enum):
    """Freshness state of underlying telemetry and financial data."""
    FRESH = "FRESH"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class ValidationFailureReason(str, Enum):
    """Explicit taxonomy of deterministic AI validation gate failure reasons."""
    SCHEMA_VIOLATION = "SCHEMA_VIOLATION"
    CONFIDENCE_PROHIBITED = "CONFIDENCE_PROHIBITED"
    UNRESOLVED_CITATION = "UNRESOLVED_CITATION"
    NUMERIC_TOLERANCE_EXCEEDED = "NUMERIC_TOLERANCE_EXCEEDED"
    EPISTEMIC_UPGRADE_ATTEMPT = "EPISTEMIC_UPGRADE_ATTEMPT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"


# Permitted scopes per question category (Correction 8: Multi-scope mapping)
QUESTION_CATEGORY_ALLOWED_SCOPES: dict[QuestionCategory, set[ScopeType]] = {
    QuestionCategory.SPEND_OVERVIEW: {ScopeType.DASHBOARD, ScopeType.ACCOUNT, ScopeType.SERVICE},
    QuestionCategory.SPEND_CHANGE: {ScopeType.DASHBOARD, ScopeType.ACCOUNT, ScopeType.SERVICE},
    QuestionCategory.COST_DRIVER: {ScopeType.DASHBOARD, ScopeType.ACCOUNT, ScopeType.SERVICE, ScopeType.RESOURCE},
    QuestionCategory.ANOMALY: {ScopeType.DASHBOARD, ScopeType.ACCOUNT, ScopeType.SERVICE, ScopeType.RESOURCE},
    QuestionCategory.OPTIMIZATION: {ScopeType.DASHBOARD, ScopeType.RECOMMENDATION, ScopeType.RESOURCE},
    QuestionCategory.RESOURCE: {ScopeType.RESOURCE},
    QuestionCategory.TELEMETRY: {ScopeType.RESOURCE},
    QuestionCategory.SCENARIO: {ScopeType.SCENARIO, ScopeType.RECOMMENDATION, ScopeType.DASHBOARD},
    QuestionCategory.FORECAST: {ScopeType.DASHBOARD, ScopeType.ACCOUNT, ScopeType.SERVICE},
    QuestionCategory.ACCOUNT: {ScopeType.ACCOUNT, ScopeType.DASHBOARD},
    QuestionCategory.SERVICE: {ScopeType.SERVICE, ScopeType.DASHBOARD},
    QuestionCategory.GENERAL_ATLAS: {
        ScopeType.DASHBOARD,
        ScopeType.ACCOUNT,
        ScopeType.SERVICE,
        ScopeType.RESOURCE,
        ScopeType.RECOMMENDATION,
        ScopeType.SCENARIO,
    },
    QuestionCategory.UNSUPPORTED: {
        ScopeType.DASHBOARD,
        ScopeType.ACCOUNT,
        ScopeType.SERVICE,
        ScopeType.RESOURCE,
        ScopeType.RECOMMENDATION,
        ScopeType.SCENARIO,
    },
}


class RetrievalErrorCode(str, Enum):
    """Explicit taxonomy of deterministic evidence retrieval and scoping error codes."""
    AUTHORIZATION_DENIED = "AUTHORIZATION_DENIED"
    INVALID_SCOPE = "INVALID_SCOPE"
    UNSUPPORTED_QUESTION = "UNSUPPORTED_QUESTION"
    EVIDENCE_NOT_FOUND = "EVIDENCE_NOT_FOUND"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    CONTEXT_LIMIT_EXCEEDED = "CONTEXT_LIMIT_EXCEEDED"
    CANONICALIZATION_ERROR = "CANONICALIZATION_ERROR"
    INVALID_EVIDENCE = "INVALID_EVIDENCE"


