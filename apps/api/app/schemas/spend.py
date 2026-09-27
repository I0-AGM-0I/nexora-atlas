"""
NEXORA ATLAS - Spend Explorer API Schemas
"""

from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.dashboard import SpendTrendPoint, ServiceBreakdownItem, AccountBreakdownItem


class ResourceSpendItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resource_id: str
    native_id: str
    resource_name: str
    service_name: str
    resource_type: str
    account_name: str
    region: str
    spend: Decimal
    percentage_of_total: Decimal


class SpendExplorerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period_days: int
    start_date: str
    end_date: str
    total_spend: Decimal
    previous_period_spend: Optional[Decimal] = None
    period_change_pct: Optional[Decimal] = None
    currency: str
    trend: List[SpendTrendPoint]
    service_breakdown: List[ServiceBreakdownItem]
    account_breakdown: List[AccountBreakdownItem]
    resource_items: List[ResourceSpendItem]
    total_resources: int
    page: int
    page_size: int
    total_pages: int
