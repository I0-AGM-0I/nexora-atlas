"""
NEXORA ATLAS - AI Explanation API Endpoints (Phase 9)
Exposes natural language interrogation, audit provenance logs, and AI status.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.services.tenant import TenantContext, get_tenant_context
from app.ai.constants import (
    AI_SYSTEM_VERSION,
    PROMPT_SYSTEM_VERSION,
)
from app.ai.orchestration.engine import AIEngine
from app.models.ai import AIInteraction
from app.schemas.ai import (
    AIAskRequest,
    AIAskResponse,
    AIStatusResponse,
    AIInteractionDetailResponse,
)

router = APIRouter(prefix="/ai", tags=["AI Explanation Engine"])


@router.post("/ask", response_model=AIAskResponse)
async def ask_atlas(
    request: AIAskRequest,
    org_slug: Optional[str] = None,
    session: AsyncSession = Depends(get_db),
) -> AIAskResponse:
    """
    Asks a natural language question about technology spending, telemetry, or optimization.
    Returns a validated, evidence-grounded explanation.
    """
    tenant = await get_tenant_context(session, org_slug)
    return await AIEngine.ask(
        session=session,
        tenant=tenant,
        request=request,
    )


@router.get("/interactions/{interaction_id}", response_model=AIInteractionDetailResponse)
async def get_interaction_audit(
    interaction_id: str,
    org_slug: Optional[str] = None,
    session: AsyncSession = Depends(get_db),
) -> AIInteractionDetailResponse:
    """
    Retrieves full audit log and provenance metadata for an AI explanation.
    """
    tenant = await get_tenant_context(session, org_slug)
    query = (
        select(AIInteraction)
        .where(
            AIInteraction.id == interaction_id,
            AIInteraction.organization_id == tenant.org_id,
        )
    )
    result = await session.execute(query)
    record = result.scalars().first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interaction audit record '{interaction_id}' not found.",
        )

    return AIInteractionDetailResponse(
        id=record.id,
        organization_id=record.organization_id,
        session_id=record.session_id,
        question=record.question,
        question_category=record.question_category,
        scope_type=record.scope_type,
        scope_id=record.scope_id,
        provider=record.provider,
        model=record.model,
        prompt_version=record.prompt_version,
        context_version=record.context_version,
        evidence_hash=record.evidence_hash,
        evidence_ids=record.evidence_ids or [],
        response_status=record.response_status,
        answer_json=record.answer_json,
        sanitized_evidence_preview=record.sanitized_evidence_preview,
        latency_ms=record.latency_ms,
        input_token_count=record.input_token_count,
        output_token_count=record.output_token_count,
        estimated_cost_usd=record.estimated_cost_usd,
        evidence_count=record.evidence_count,
        error_code=record.error_code,
        error_message=record.error_message,
        created_at=record.created_at,
    )


@router.get("/status", response_model=AIStatusResponse)
async def get_ai_status() -> AIStatusResponse:
    """
    Reports operational status and configuration of the AI explanation subsystem.
    """
    return AIStatusResponse(
        ai_enabled=settings.AI_ENABLED,
        provider=settings.AI_PROVIDER,
        model=settings.AI_MODEL if settings.AI_PROVIDER == "openai" else "mock-deterministic",
        max_context_tokens=settings.AI_MAX_CONTEXT_TOKENS,
        max_output_tokens=settings.AI_MAX_OUTPUT_TOKENS,
        rate_limit_per_minute=settings.MAX_AI_REQUESTS_PER_MINUTE,
        system_version=AI_SYSTEM_VERSION,
        prompt_version=PROMPT_SYSTEM_VERSION,
        is_offline_capable=True,
    )
