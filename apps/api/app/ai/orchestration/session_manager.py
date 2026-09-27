"""
NEXORA ATLAS - Session Context Manager (Phase 9)
Maintains bounded conversational memory strictly for conversational intent and disambiguation.
PRESERVATION INVARIANT: Previous assistant answers are NEVER used as authoritative evidence;
fresh evidence is always retrieved from Atlas deterministic engines.
"""

from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AIInteraction
from app.ai.constants import (
    MAX_SESSION_MESSAGES,
    MAX_SESSION_CONTEXT_TOKENS,
    SESSION_RETENTION_HOURS,
)


class SessionManager:
    """Manages bounded session conversation context for AI queries."""

    @classmethod
    async def get_session_history(
        cls,
        session: AsyncSession,
        organization_id: str,
        session_id: str,
    ) -> List[Dict[str, str]]:
        """
        Retrieves recent turns from past AIInteractions within the retention window.
        Returns messages strictly for intent resolution.
        """
        if not session_id:
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(hours=SESSION_RETENTION_HOURS)

        query = (
            select(AIInteraction)
            .where(
                AIInteraction.organization_id == organization_id,
                AIInteraction.session_id == session_id,
                AIInteraction.created_at >= cutoff,
            )
            .order_by(AIInteraction.created_at.desc())
            .limit(MAX_SESSION_MESSAGES)
        )

        res = await session.execute(query)
        past_interactions = list(res.scalars().all())
        past_interactions.reverse()  # Chronological order

        history: List[Dict[str, str]] = []
        for inter in past_interactions:
            history.append({"role": "user", "content": inter.question})
            if inter.answer_json and "summary" in inter.answer_json:
                history.append({"role": "assistant", "content": str(inter.answer_json["summary"])})

        # Trim if excessive tokens (approx 4 chars per token)
        max_chars = MAX_SESSION_CONTEXT_TOKENS * 4
        total_chars = sum(len(m["content"]) for m in history)
        while total_chars > max_chars and len(history) > 2:
            removed = history.pop(0)
            total_chars -= len(removed["content"])

        return history
