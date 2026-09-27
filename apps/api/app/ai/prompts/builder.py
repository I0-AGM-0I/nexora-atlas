"""
NEXORA ATLAS - Prompt Builder (Phase 9 Milestone 3)
Assembles immutable AIProviderRequest envelopes combining system prompt,
user question, bounded context, and cryptographic evidence hash.
"""

import uuid
from typing import List, Dict, Optional, Any

from app.core.config import settings
from app.ai.models import BoundedContext, EvidencePackage
from app.ai.context.builder import ContextBuilder
from app.ai.providers.models import AIProviderRequest
from app.ai.prompts.system import build_system_prompt
from app.ai.prompts.templates import build_user_prompt
from app.ai.prompts.versions import PROMPT_SYSTEM_VERSION, CONTEXT_VERSION


class PromptBuilder:
    """
    Factory for constructing validated AIProviderRequest envelopes.
    Ensures prompt versioning, context boundary tagging, and evidence hash propagation.
    """

    @classmethod
    def build_request(
        cls,
        question: str,
        bounded_context: Optional[BoundedContext] = None,
        evidence_package: Optional[EvidencePackage] = None,
        session_history: Optional[List[Dict[str, str]]] = None,
        model: Optional[str] = None,
        request_id: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> AIProviderRequest:
        """
        Builds a complete AIProviderRequest envelope.
        Extracts or computes BoundedContext from evidence_package if needed.
        """
        # Ensure BoundedContext is resolved
        if bounded_context is None:
            if evidence_package is not None:
                bounded_context = ContextBuilder.create_bounded_context(evidence_package)
            else:
                raise ValueError("Either bounded_context or evidence_package must be provided.")

        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(
            question=question,
            context=bounded_context,
            session_history=session_history,
        )

        req_id = request_id or str(uuid.uuid4())
        configured_model = model or settings.AI_MODEL
        configured_max_tokens = max_tokens or settings.AI_MAX_OUTPUT_TOKENS

        return AIProviderRequest(
            question=question,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            bounded_context=bounded_context,
            context_json=bounded_context.canonical_json,
            evidence_hash=bounded_context.sha256_hash,
            prompt_version=PROMPT_SYSTEM_VERSION,
            context_version=CONTEXT_VERSION,
            model=configured_model,
            request_id=req_id,
            temperature=temperature,
            max_tokens=configured_max_tokens,
        )
