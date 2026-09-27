"""
NEXORA ATLAS - AI Provider Protocol & Base Classes (Phase 9 Milestone 3)
Defines the abstract interface for all AI explanation backends.
Decouples Atlas domain engines from external LLM APIs.
"""

from typing import Protocol, List, Dict, Any, Optional, runtime_checkable
from app.ai.models import EvidencePackage, AIResponse
from app.ai.providers.models import AIProviderRequest, AIProviderResult


@runtime_checkable
class AIProvider(Protocol):
    """
    Protocol for AI explanation providers.
    Every implementation receives an AIProviderRequest (containing M2 BoundedContext)
    and returns an AIProviderResult containing an untrusted candidate explanation.
    """

    async def generate_candidate(
        self,
        request: AIProviderRequest,
    ) -> AIProviderResult:
        """Generates an untrusted candidate explanation grounded strictly in the request."""
        ...

    async def generate_explanation(
        self,
        question: str,
        evidence_package: EvidencePackage,
        session_history: Optional[List[Dict[str, str]]] = None,
    ) -> AIResponse:
        """Dual-compatibility method conforming to existing AIProviderContract."""
        ...
