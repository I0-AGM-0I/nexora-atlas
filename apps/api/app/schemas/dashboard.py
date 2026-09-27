"""
NEXORA ATLAS - Dashboard API Schemas
"""

from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class DemoEventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    occurred_at: str
    title: str
    description: str
    category: str
    impact_service: str
    related_resource_native_id: Optional[str] = None


class DashboardSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    organization_name: str
    total_spend: Decimal = Field(..., description="Sum of all CostRecords over the 90-day history")
    monthly_run_rate: Decimal = Field(..., description="Sum of CostRecords over latest 30 calendar days")
    previous_30d_spend: Decimal = Field(..., description="Sum of CostRecords from day -60 to -31")
    run_rate_change_pct: Optional[Decimal] = Field(None, description="((current - previous) / previous) * 100")
    potential_monthly_savings: Decimal = Field(..., description="Sum of active optimization opportunities")
    potential_annual_savings: Decimal = Field(..., description="Monthly savings * 12")
    active_anomalies: int
    total_resources: int
    total_accounts: int
    currency: str
    max_date: str
    min_date: str
    is_demo: bool


class SpendTrendPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: str
    spend: Decimal
    cumulative_spend: Decimal
    events: List[DemoEventSchema] = []


class SpendTrendResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    points: List[SpendTrendPoint]
    total_spend: Decimal
    period_days: int
    currency: str


class ServiceBreakdownItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    service_name: str
    total_spend: Decimal
    percentage: Decimal


class ServiceBreakdownResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[ServiceBreakdownItem]
    total_spend: Decimal
    currency: str


class AccountBreakdownItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: str
    account_name: str
    provider_account_id: str
    total_spend: Decimal
    percentage: Decimal


class AccountBreakdownResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[AccountBreakdownItem]
    total_spend: Decimal
    currency: str


class RecentActivityItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    timestamp: str
    action: str
    entity_type: str
    actor_id: str
    metadata_json: Optional[Dict[str, Any]] = None


class RecentActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[RecentActivityItem]
