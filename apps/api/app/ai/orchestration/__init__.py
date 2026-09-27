"""
NEXORA ATLAS - AI Explanation Orchestration Subsystem (Phase 9 Milestone 4)
Exports the orchestration engine, regeneration request builder, and safe fallbacks.
"""

from app.ai.orchestration.regeneration import (
    build_regeneration_request,
    is_eligible_for_regeneration,
    REGENERATION_ELIGIBLE_STATUSES,
)
from app.ai.orchestration.fallback import (
    build_safe_failure,
    build_provider_failure,
    build_deterministic_fallback,
    SAFE_FAILURE_EXPLANATION,
)
from app.ai.orchestration.engine import AIExplanationOrchestrator, AIEngine

__all__ = [
    "AIExplanationOrchestrator",
    "AIEngine",
    "build_regeneration_request",
    "is_eligible_for_regeneration",
    "REGENERATION_ELIGIBLE_STATUSES",
    "build_safe_failure",
    "build_provider_failure",
    "build_deterministic_fallback",
    "SAFE_FAILURE_EXPLANATION",
]
