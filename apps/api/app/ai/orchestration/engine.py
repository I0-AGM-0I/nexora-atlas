"""
NEXORA ATLAS - AI Explanation Orchestration Engine (Phase 9 Milestone 4)
Coordinates the end-to-end pipeline:
Bounded Context -> AI Provider -> Untrusted Candidate -> Validation Gate -> Verified Answer / Safe Failure
Enforces strict provider error isolation, single controlled regeneration, and bounded invocation counts (<= 2).
"""

import time
from typing import Optional, List, Dict, Any
from decimal import Decimal

from app.ai.types import AIResponseStatus, ProviderErrorCode
from app.ai.models import EvidencePackage, AIResponse, AIAnswer
from app.ai.providers.base import AIProvider
from app.ai.providers.models import AIProviderRequest, AIProviderResult, AICandidateAnswer
from app.ai.validation.result import ValidationResult, ValidationStatus
from app.ai.validation.validator import ResponseValidator
from app.ai.orchestration.regeneration import (
    is_eligible_for_regeneration,
    build_regeneration_request,
)
from app.ai.orchestration.fallback import (
    build_safe_failure,
    build_provider_failure,
    build_deterministic_fallback,
)


class AIExplanationOrchestrator:
    """
    Master orchestrator governing the interaction between AI providers and the Atlas validation gate.
    Answers: 'What should Atlas do with this result?'
    """

    MAX_REGENERATIONS = 1

    @classmethod
    async def orchestrate(
        cls,
        request: AIProviderRequest,
        provider: AIProvider,
        evidence_package: EvidencePackage,
        allow_regeneration: bool = True,
    ) -> AIResponse:
        """
        Executes the explanation lifecycle:
        1. Invokes provider for initial candidate.
        2. Isolates provider errors from validation failures.
        3. Runs ResponseValidator across all 8 gates.
        4. If invalid and eligible, performs at most ONE controlled regeneration.
        5. Returns verified AIAnswer or safe failure.
        """
        start_time = time.monotonic()
        invocation_count = 0
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost = Decimal("0.0")

        # ----------------------------------------------------------------------
        # Step 1: First Candidate Generation
        # ----------------------------------------------------------------------
        invocation_count += 1
        res1: AIProviderResult = await provider.generate_candidate(request)

        total_input_tokens += res1.input_tokens
        total_output_tokens += res1.output_tokens
        total_cost += res1.estimated_cost_usd

        # Step 2: Handle Provider Failures (Timeout, Auth, Rate Limit, Outage)
        if res1.status != AIResponseStatus.COMPLETED or not res1.candidate_answer:
            return build_provider_failure(res1)

        candidate1 = res1.candidate_answer

        # ----------------------------------------------------------------------
        # Step 3: Validate Candidate 1 through all 8 gates
        # ----------------------------------------------------------------------
        val1: ValidationResult = ResponseValidator.validate(
            candidate=candidate1,
            evidence_package=evidence_package,
            evidence_hash=request.evidence_hash,
        )

        if val1.is_valid and val1.verified_answer:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return AIResponse(
                status=AIResponseStatus.COMPLETED,
                answer=val1.verified_answer,
                raw_text=val1.verified_answer.answer,
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
                latency_ms=elapsed_ms,
                estimated_cost_usd=total_cost,
            )

        # ----------------------------------------------------------------------
        # Step 4: One Controlled Regeneration (if eligible)
        # ----------------------------------------------------------------------
        can_regenerate = (
            allow_regeneration
            and invocation_count < (1 + cls.MAX_REGENERATIONS)
            and is_eligible_for_regeneration(val1)
        )

        if can_regenerate:
            regen_request = build_regeneration_request(
                original_request=request,
                candidate=candidate1,
                validation_result=val1,
            )

            invocation_count += 1
            res2: AIProviderResult = await provider.generate_candidate(regen_request)

            total_input_tokens += res2.input_tokens
            total_output_tokens += res2.output_tokens
            total_cost += res2.estimated_cost_usd

            # If provider failed on regeneration attempt, return provider failure
            if res2.status != AIResponseStatus.COMPLETED or not res2.candidate_answer:
                return build_provider_failure(res2)

            candidate2 = res2.candidate_answer

            # Validate Candidate 2
            val2: ValidationResult = ResponseValidator.validate(
                candidate=candidate2,
                evidence_package=evidence_package,
                evidence_hash=request.evidence_hash,
            )

            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            if val2.is_valid and val2.verified_answer:
                return AIResponse(
                    status=AIResponseStatus.COMPLETED,
                    answer=val2.verified_answer,
                    raw_text=val2.verified_answer.answer,
                    input_tokens=total_input_tokens,
                    output_tokens=total_output_tokens,
                    latency_ms=elapsed_ms,
                    estimated_cost_usd=total_cost,
                )
            else:
                # Second candidate also failed -> Emit Safe Failure
                res2_accumulated = AIProviderResult(
                    status=res2.status,
                    provider=res2.provider,
                    model=res2.model or "mock",
                    input_tokens=total_input_tokens,
                    output_tokens=total_output_tokens,
                    latency_ms=elapsed_ms,
                    estimated_cost_usd=total_cost,
                )
                return build_safe_failure(val2, res2_accumulated, regeneration_count=1)

        # Non-regenerable failure -> Emit Safe Failure
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        res1_accumulated = AIProviderResult(
            status=res1.status,
            provider=res1.provider,
            model=res1.model or "mock",
            input_tokens=total_input_tokens,
            output_tokens=total_output_tokens,
            latency_ms=elapsed_ms,
            estimated_cost_usd=total_cost,
        )
        return build_safe_failure(val1, res1_accumulated, regeneration_count=0)


class AIEngine:
    """
    High-level facade for API ask endpoints and legacy compatibility tests.
    Routes queries through authorization, retrieval, context building, prompting, and orchestrator.
    """

    @classmethod
    async def ask(
        cls,
        session: Any,
        tenant: Any,
        request: Any,
    ) -> Any:
        import uuid
        from datetime import datetime, timezone
        from app.core.config import settings
        from app.schemas.ai import AIAskResponse
        from app.ai.models import DataFreshness

        if not getattr(settings, "AI_ENABLED", False):
            ans = AIAnswer(
                summary="AI features are disabled by configuration in this environment.",
                answer="AI natural language intelligence is currently disabled by system configuration.",
                conclusions=[],
                limitations=["AI provider integration is disabled."],
                recommended_next_steps=["Enable AI_ENABLED in configuration to activate explanations."],
                cited_entities=[],
                epistemic_notes=["Subsystem offline."],
            )
            return AIAskResponse(
                interaction_id=str(uuid.uuid4()),
                session_id=request.session_id or str(uuid.uuid4()),
                status=AIResponseStatus.DISABLED,
                question=request.question,
                scope_type=request.scope_type,
                scope_id=request.scope_id,
                answer=ans,
                evidence_hash="0" * 64,
                evidence_count=0,
                evidence_ids=[],
                data_freshness=DataFreshness(),
                latency_ms=0,
                token_count=0,
                estimated_cost_usd=Decimal("0.0"),
                error_code="DISABLED",
                error_message="AI features are disabled by configuration.",
                created_at=datetime.now(timezone.utc),
            )

        from app.ai.retrieval.scope import authorize_scope
        from app.ai.retrieval.query_router import classify_query
        from app.ai.retrieval.engine import EvidenceRetrievalEngine
        from app.ai.context.builder import ContextBuilder
        from app.ai.prompts.builder import PromptBuilder
        from app.ai.providers.registry import get_provider

        auth_scope = await authorize_scope(
            session=session,
            tenant=tenant,
            scope_type=request.scope_type,
            scope_id=request.scope_id,
        )
        intent = classify_query(request.question)
        evidence_pkg = await EvidenceRetrievalEngine.retrieve(
            session=session,
            auth_scope=auth_scope,
            intent=intent,
        )
        context = ContextBuilder.build_context(evidence_pkg)
        provider_req = PromptBuilder.build_request(
            question=request.question,
            evidence_package=evidence_pkg,
            bounded_context=context,
        )
        provider = get_provider()
        ai_resp = await AIExplanationOrchestrator.orchestrate(
            request=provider_req,
            provider=provider,
            evidence_package=evidence_pkg,
        )

        return AIAskResponse(
            interaction_id=str(uuid.uuid4()),
            session_id=request.session_id or str(uuid.uuid4()),
            status=ai_resp.status,
            question=request.question,
            scope_type=request.scope_type,
            scope_id=request.scope_id,
            answer=ai_resp.answer,
            evidence_hash=context.sha256_hash,
            evidence_count=evidence_pkg.evidence_count,
            evidence_ids=[item.id for item in evidence_pkg.all_items()],
            data_freshness=evidence_pkg.freshness,
            latency_ms=ai_resp.latency_ms,
            token_count=ai_resp.total_tokens if hasattr(ai_resp, "total_tokens") else 0,
            estimated_cost_usd=ai_resp.estimated_cost_usd,
            error_code=ai_resp.error_code.value if ai_resp.error_code else None,
            error_message=ai_resp.error_message,
            created_at=datetime.now(timezone.utc),
        )
