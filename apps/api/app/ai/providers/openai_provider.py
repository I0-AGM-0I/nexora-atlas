"""
NEXORA ATLAS - OpenAI Provider (Phase 9 Milestone 3)
Production async provider communicating with OpenAI-compatible endpoints via httpx.
Encapsulates all vendor-specific protocols, structured JSON decoding,
token calculation, and explicit error taxonomy.
"""

import json
import time
from typing import List, Dict, Any, Optional
from decimal import Decimal
import httpx

from app.core.config import settings
from app.ai.types import AIResponseStatus, EpistemicClass
from app.ai.models import EvidencePackage, AIResponse, AIAnswer, AIConclusion, NumericClaim
from app.ai.constants import (
    INPUT_COST_PER_1K_TOKENS,
    OUTPUT_COST_PER_1K_TOKENS,
)
from app.ai.providers.errors import (
    ProviderErrorCode,
    ProviderTimeoutError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderUnavailableError,
    ProviderInvalidResponseError,
    ProviderUnknownError,
)
from app.ai.providers.models import (
    AIProviderRequest,
    AIProviderResult,
    AICandidateAnswer,
    AICandidateConclusion,
    AICandidateCitation,
    AICandidateNumericClaim,
)


class OpenAIProvider:
    """
    Direct async OpenAI API client using httpx.
    Guarantees strict isolation from the rest of the Atlas codebase.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: Optional[int] = None,
    ):
        self.api_key = api_key or settings.AI_API_KEY
        self.model = model or settings.AI_MODEL
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds or settings.AI_TIMEOUT_SECONDS

    async def generate_candidate(
        self,
        request: AIProviderRequest,
    ) -> AIProviderResult:
        """
        Primary M3 invocation method: Dispatches request to OpenAI API
        and extracts unvalidated AICandidateAnswer.
        """
        start_time = time.monotonic()

        # Invariant: AI_ENABLED=false is a hard stop; do not accidentally activate
        if not settings.AI_ENABLED:
            return AIProviderResult(
                status=AIResponseStatus.PROVIDER_ERROR,
                provider="openai",
                model=request.model or self.model,
                request_id=request.request_id,
                evidence_hash=request.evidence_hash,
                error_code=ProviderErrorCode.PROVIDER_UNAVAILABLE,
                error_message="AI is currently disabled (AI_ENABLED=false). Cannot invoke OpenAI provider.",
                latency_ms=0,
            )

        # Check API key configuration
        if not self.api_key:
            return AIProviderResult(
                status=AIResponseStatus.PROVIDER_ERROR,
                provider="openai",
                model=request.model or self.model,
                request_id=request.request_id,
                evidence_hash=request.evidence_hash,
                error_code=ProviderErrorCode.AUTHENTICATION_ERROR,
                error_message="OpenAI API key is not configured. Set AI_API_KEY environment variable.",
                latency_ms=0,
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": request.model or self.model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        endpoint = f"{self.base_url}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=float(self.timeout_seconds)) as client:
                response = await client.post(endpoint, json=payload, headers=headers)

            elapsed_ms = int((time.monotonic() - start_time) * 1000)

            # Check HTTP Status Codes
            if response.status_code in (401, 403):
                raise ProviderAuthenticationError(
                    message=f"Authentication failed with OpenAI API (HTTP {response.status_code}).",
                    raw_status_code=response.status_code,
                )
            elif response.status_code == 429:
                raise ProviderRateLimitError(
                    message="OpenAI rate limit exceeded. Please retry shortly.",
                    raw_status_code=429,
                )
            elif response.status_code >= 500:
                raise ProviderUnavailableError(
                    message=f"OpenAI service unavailable (HTTP {response.status_code}).",
                    raw_status_code=response.status_code,
                )
            elif response.status_code != 200:
                raise ProviderUnknownError(
                    message=f"OpenAI API returned unexpected HTTP status {response.status_code}.",
                    raw_status_code=response.status_code,
                )

            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                raise ProviderInvalidResponseError("OpenAI API returned empty choices list.")

            content_str = choices[0].get("message", {}).get("content", "")
            if not content_str:
                raise ProviderInvalidResponseError("OpenAI API returned empty message content.")

            # Parse JSON content into untrusted candidate answer
            try:
                content_json = json.loads(content_str)
            except json.JSONDecodeError as jde:
                raise ProviderInvalidResponseError(f"Failed to parse OpenAI JSON response: {jde}")

            candidate = self._parse_candidate_dict(content_json)

            # Authoritative token accounting from OpenAI response
            usage = data.get("usage", {})
            input_tokens = int(usage.get("prompt_tokens", 0))
            output_tokens = int(usage.get("completion_tokens", 0))
            total_tokens = int(usage.get("total_tokens", input_tokens + output_tokens))

            # Decimal token cost calculation
            estimated_cost = (
                (Decimal(input_tokens) / Decimal(1000) * INPUT_COST_PER_1K_TOKENS)
                + (Decimal(output_tokens) / Decimal(1000) * OUTPUT_COST_PER_1K_TOKENS)
            )

            return AIProviderResult(
                status=AIResponseStatus.COMPLETED,
                provider="openai",
                model=request.model or self.model,
                candidate_answer=candidate,
                raw_response_text=content_str,
                raw_response_metadata={
                    "openai_id": data.get("id"),
                    "finish_reason": choices[0].get("finish_reason"),
                },
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                estimated_cost_usd=estimated_cost,
                latency_ms=elapsed_ms,
                request_id=request.request_id,
                evidence_hash=request.evidence_hash,
            )

        except httpx.TimeoutException:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return AIProviderResult(
                status=AIResponseStatus.PROVIDER_ERROR,
                provider="openai",
                model=request.model or self.model,
                request_id=request.request_id,
                evidence_hash=request.evidence_hash,
                error_code=ProviderErrorCode.TIMEOUT,
                error_message=f"OpenAI request timed out after {self.timeout_seconds} seconds.",
                latency_ms=elapsed_ms,
            )
        except ProviderAuthenticationError as pae:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return AIProviderResult(
                status=AIResponseStatus.PROVIDER_ERROR,
                provider="openai",
                model=request.model or self.model,
                request_id=request.request_id,
                evidence_hash=request.evidence_hash,
                error_code=pae.error_code,
                error_message=pae.message,
                latency_ms=elapsed_ms,
            )
        except ProviderRateLimitError as prle:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return AIProviderResult(
                status=AIResponseStatus.RATE_LIMITED,
                provider="openai",
                model=request.model or self.model,
                request_id=request.request_id,
                evidence_hash=request.evidence_hash,
                error_code=prle.error_code,
                error_message=prle.message,
                latency_ms=elapsed_ms,
            )
        except ProviderUnavailableError as pue:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return AIProviderResult(
                status=AIResponseStatus.PROVIDER_ERROR,
                provider="openai",
                model=request.model or self.model,
                request_id=request.request_id,
                evidence_hash=request.evidence_hash,
                error_code=pue.error_code,
                error_message=pue.message,
                latency_ms=elapsed_ms,
            )
        except ProviderInvalidResponseError as pire:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return AIProviderResult(
                status=AIResponseStatus.PROVIDER_ERROR,
                provider="openai",
                model=request.model or self.model,
                request_id=request.request_id,
                evidence_hash=request.evidence_hash,
                error_code=pire.error_code,
                error_message=pire.message,
                latency_ms=elapsed_ms,
            )
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return AIProviderResult(
                status=AIResponseStatus.PROVIDER_ERROR,
                provider="openai",
                model=request.model or self.model,
                request_id=request.request_id,
                evidence_hash=request.evidence_hash,
                error_code=ProviderErrorCode.UNKNOWN,
                error_message=f"Unexpected error communicating with OpenAI: {str(exc)}",
                latency_ms=elapsed_ms,
            )

    async def generate_explanation(
        self,
        question: str,
        evidence_package: EvidencePackage,
        session_history: Optional[List[Dict[str, str]]] = None,
    ) -> AIResponse:
        """
        Dual-compatibility method conforming to existing AIProviderContract.
        """
        from app.ai.prompts.builder import PromptBuilder

        req = PromptBuilder.build_request(
            question=question,
            evidence_package=evidence_package,
            session_history=session_history,
        )
        res = await self.generate_candidate(req)

        ans = None
        if res.candidate_answer:
            conclusions = [
                AIConclusion(
                    statement=c.statement,
                    epistemic_class=c.epistemic_class,
                    evidence_ids=c.evidence_ids,
                    numeric_claims=[
                        NumericClaim(value=nc.value, unit=nc.unit, evidence_id=nc.evidence_id)
                        for nc in c.numeric_claims
                    ],
                )
                for c in res.candidate_answer.conclusions
            ]
            ans = AIAnswer(
                summary=res.candidate_answer.summary,
                answer=res.candidate_answer.answer,
                conclusions=conclusions,
                limitations=res.candidate_answer.limitations,
                recommended_next_steps=res.candidate_answer.recommended_next_steps,
                cited_entities=[],
                epistemic_notes=res.candidate_answer.epistemic_notes,
                freshness_note=res.candidate_answer.freshness_note,
            )

        return AIResponse(
            status=res.status,
            answer=ans,
            error_code=res.error_code,
            error_message=res.error_message,
            input_tokens=res.input_tokens,
            output_tokens=res.output_tokens,
            total_tokens=res.total_tokens,
            latency_ms=res.latency_ms,
            estimated_cost_usd=res.estimated_cost_usd,
        )

    def _parse_candidate_dict(self, d: Dict[str, Any]) -> AICandidateAnswer:
        """Parses a dictionary from model JSON output into AICandidateAnswer."""
        conclusions: List[AICandidateConclusion] = []
        for c in d.get("conclusions", []):
            if isinstance(c, dict):
                claims = []
                for claim in c.get("numeric_claims", []):
                    if isinstance(claim, dict):
                        claims.append(
                            AICandidateNumericClaim(
                                value=Decimal(str(claim.get("value", 0))),
                                unit=str(claim.get("unit", "")),
                                evidence_id=str(claim.get("evidence_id", "")),
                            )
                        )
                # Map or default epistemic class
                ep_raw = str(c.get("epistemic_class", "INFERRED")).upper()
                try:
                    ep_class = EpistemicClass(ep_raw)
                except ValueError:
                    ep_class = EpistemicClass.INFERRED

                conclusions.append(
                    AICandidateConclusion(
                        statement=str(c.get("statement", "")),
                        epistemic_class=ep_class,
                        evidence_ids=[str(i) for i in c.get("evidence_ids", [])],
                        numeric_claims=claims,
                    )
                )

        citations: List[AICandidateCitation] = []
        for cit in d.get("cited_entities", []):
            if isinstance(cit, dict):
                citations.append(
                    AICandidateCitation(
                        id=str(cit.get("id", "")),
                        title=str(cit.get("title", "")),
                        entity_type=str(cit.get("entity_type", "")),
                        entity_id=str(cit.get("entity_id", "")),
                        link_path=cit.get("link_path"),
                    )
                )

        return AICandidateAnswer(
            summary=str(d.get("summary", "")),
            answer=str(d.get("answer", "")),
            conclusions=conclusions,
            limitations=[str(l) for l in d.get("limitations", [])],
            recommended_next_steps=[str(s) for s in d.get("recommended_next_steps", [])],
            cited_entities=citations,
            epistemic_notes=[str(n) for n in d.get("epistemic_notes", [])],
            freshness_note=d.get("freshness_note"),
            raw_json=d,
        )
