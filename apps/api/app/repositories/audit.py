"""
NEXORA ATLAS - AuditLog Repository
Enforces append-only immutable audit recording.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.organization import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(AuditLog, session)

    async def log_event(
        self,
        org_id: str,
        actor_id: str,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Appends an immutable audit log entry."""
        log_entry = AuditLog(
            org_id=org_id,
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=metadata_json,
        )
        self.session.add(log_entry)
        await self.session.commit()
        await self.session.refresh(log_entry)
        return log_entry

    async def list_recent(self, org_id: str, limit: int = 50) -> List[AuditLog]:
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.org_id == org_id)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    # Immutable guardrail
    async def delete_by_id(self, entity_id: str) -> bool:
        raise NotImplementedError("AuditLog records are append-only and cannot be deleted.")

    async def update(self, entity: AuditLog) -> AuditLog:
        raise NotImplementedError("AuditLog records are immutable and cannot be updated.")
