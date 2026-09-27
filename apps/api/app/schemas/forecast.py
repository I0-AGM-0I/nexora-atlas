"""
NEXORA ATLAS - Forecast API Schemas
"""

from decimal import Decimal
from typing import List
from pydantic import BaseModel, ConfigDict


class ForecastItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    account_name: str
    forecast_month: str
    projected_cost: Decimal
    lower_bound: Decimal
    upper_bound: Decimal
    confidence_pct: Decimal
    algorithm: str
    is_synthetic: bool = True


class ForecastResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    disclaimer: str
    forecasts: List[ForecastItem]
