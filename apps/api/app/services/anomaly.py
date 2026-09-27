"""
NEXORA ATLAS - Anomaly Service
Maintains strict structural separation between Observed Data (facts) and Inferences (hypotheses).
"""

from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.anomaly import Anomaly
from app.services.tenant import TenantContext
from app.schemas.anomaly import (
    AnomalyItem,
    AnomalyObservedFacts,
    AnomalyInferredAnalysis,
    AnomalyListResponse,
)


class AnomalyService:
    @classmethod
    def _to_schema(cls, anom: Anomaly, account_name_map: dict) -> AnomalyItem:
        return AnomalyItem(
            id=anom.id,
            account_id=anom.account_id,
            account_name=account_name_map.get(anom.account_id, "Unknown"),
            resource_id=anom.resource_id,
            resource_name=anom.resource.name if anom.resource else None,
            resource_native_id=anom.resource.native_id if anom.resource else None,
            service_name=anom.service_name,
            observed=AnomalyObservedFacts(
                observed_cost=anom.observed_cost,
                baseline_cost=anom.baseline_cost,
                percentage_change=anom.percentage_change,
                detected_at=anom.detected_at.isoformat(),
                detection_rule=anom.detection_rule,
                observed_metrics_json=anom.observed_metrics_json,
            ),
            inference=AnomalyInferredAnalysis(
                severity=anom.severity,
                status=anom.status,
                inferred_cause=anom.inferred_cause,
                confidence_pct=anom.confidence_pct,
                inference_details_json=anom.inference_details_json,
            ),
        )

    @classmethod
    async def list_anomalies(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        severity: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> AnomalyListResponse:
        """Lists anomalies with optional filters by severity and status."""
        query = (
            select(Anomaly)
            .options(selectinload(Anomaly.resource))
            .where(Anomaly.account_id.in_(tenant.account_ids))
        )
        if severity:
            query = query.where(Anomaly.severity == severity.upper())
        if status_filter:
            query = query.where(Anomaly.status == status_filter.upper())

        query = query.order_by(Anomaly.detected_at.desc())
        result = await session.execute(query)
        anomalies = list(result.scalars().all())

        # Total active / open count (OPEN or ACKNOWLEDGED)
        open_count_res = await session.execute(
            select(func.count(Anomaly.id))
            .where(
                Anomaly.account_id.in_(tenant.account_ids),
                Anomaly.status.in_(["OPEN", "ACKNOWLEDGED"]),
            )
        )
        open_count = open_count_res.scalar() or 0

        items = [cls._to_schema(a, tenant.account_name_map) for a in anomalies]
        return AnomalyListResponse(
            items=items,
            total_count=len(items),
            open_count=open_count,
        )

    @classmethod
    async def get_anomaly(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
        anomaly_id: str,
    ) -> AnomalyItem:
        """Retrieves a single anomaly detail, strictly scoped to tenant accounts."""
        query = (
            select(Anomaly)
            .options(selectinload(Anomaly.resource))
            .where(
                Anomaly.id == anomaly_id,
                Anomaly.account_id.in_(tenant.account_ids),
            )
        )
        result = await session.execute(query)
        anom = result.scalars().first()
        if not anom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Anomaly with ID '{anomaly_id}' not found in current organization context.",
            )
        return cls._to_schema(anom, tenant.account_name_map)
