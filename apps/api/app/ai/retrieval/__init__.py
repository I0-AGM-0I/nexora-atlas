"""
NEXORA ATLAS - AI Retrieval Package (Phase 9)
Tenant-scoped and deterministic evidence gathering.
"""

from app.ai.retrieval.scope import authorize_scope, AuthorizationScope, ScopeAuthorizationResult
from app.ai.retrieval.query_router import classify_query, QueryIntent
from app.ai.retrieval.evidence_retriever import EvidenceRetriever
from app.ai.retrieval.selectors import (
    SpendEvidenceSelector,
    CostDriverEvidenceSelector,
    AnomalyEvidenceSelector,
    ResourceEvidenceSelector,
    TelemetryEvidenceSelector,
    RecommendationEvidenceSelector,
    ScenarioEvidenceSelector,
    ForecastEvidenceSelector,
)
from app.ai.retrieval.freshness import evaluate_package_freshness, evaluate_timestamp_freshness
from app.ai.retrieval.ranking import rank_evidence_items
from app.ai.retrieval.engine import RetrievalEngine

__all__ = [
    "authorize_scope",
    "AuthorizationScope",
    "ScopeAuthorizationResult",
    "classify_query",
    "QueryIntent",
    "EvidenceRetriever",
    "SpendEvidenceSelector",
    "CostDriverEvidenceSelector",
    "AnomalyEvidenceSelector",
    "ResourceEvidenceSelector",
    "TelemetryEvidenceSelector",
    "RecommendationEvidenceSelector",
    "ScenarioEvidenceSelector",
    "ForecastEvidenceSelector",
    "evaluate_package_freshness",
    "evaluate_timestamp_freshness",
    "rank_evidence_items",
    "RetrievalEngine",
]
