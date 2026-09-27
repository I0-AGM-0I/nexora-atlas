"""
NEXORA ATLAS - Forecast Service
Read-only exposure of synthetic demo forecast horizons.
Strictly disclaims production forecast engine until Phase 5.
"""

from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.forecast import Forecast
from app.services.tenant import TenantContext
from app.schemas.forecast import ForecastItem, ForecastResponse


class ForecastService:
    @classmethod
    async def get_forecasts(
        cls,
        session: AsyncSession,
        tenant: TenantContext,
    ) -> ForecastResponse:
        """Retrieves synthetic forecast horizons."""
        query = (
            select(Forecast)
            .where(Forecast.account_id.in_(tenant.account_ids))
            .order_by(Forecast.forecast_month.asc())
        )
        result = await session.execute(query)
        forecasts = list(result.scalars().all())

        items = [
            ForecastItem(
                id=f.id,
                account_id=f.account_id,
                account_name=tenant.account_name_map.get(f.account_id, "Unknown"),
                forecast_month=f.forecast_month.isoformat(),
                projected_cost=f.projected_cost,
                lower_bound=f.lower_bound,
                upper_bound=f.upper_bound,
                confidence_pct=f.confidence_pct,
                algorithm=f.algorithm,
                is_synthetic=True,
            )
            for f in forecasts
        ]

        return ForecastResponse(
            disclaimer="DEMO FORECAST: The predictions displayed are synthetic fixtures generated for demonstration purposes.",
            forecasts=items,
        )
