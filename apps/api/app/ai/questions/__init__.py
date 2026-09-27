"""
NEXORA ATLAS - AI Question Processing Domain (Phase 9)
Defines query classification contracts, routing, and contextual entity binding.
Note: Query classification is a routing mechanism, NOT a security boundary.
Tenant authorization MUST precede classification.
"""

from app.ai.types import QuestionCategory, QUESTION_CATEGORY_ALLOWED_SCOPES
from app.ai.contracts import QueryClassifierContract
from app.ai.questions.classifier import (
    DeterministicQuestionClassifier,
    default_classifier,
    classify_query,
    QueryIntent,
)
from app.ai.questions.scope_resolver import ScopeResolver, ResolvedScope

__all__ = [
    "QuestionCategory",
    "QUESTION_CATEGORY_ALLOWED_SCOPES",
    "QueryClassifierContract",
    "DeterministicQuestionClassifier",
    "default_classifier",
    "classify_query",
    "QueryIntent",
    "ScopeResolver",
    "ResolvedScope",
]
