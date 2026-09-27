"""
NEXORA ATLAS - Operational Telemetry API Schemas
"""

from decimal import Decimal
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class TelemetryObservationItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    timestamp: datetime
    metric_name: str
    namespace: str
    source_statistic: str
    value: Decimal
    unit: Optional[str] = None
    period: int
    dimensions_json: Dict[str, Any] = Field(default_factory=dict)


class TelemetryMetricSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    metric_name: str
    namespace: str
    unit: Optional[str] = None
    source_statistic: str
    observation_count: int
    p95: Optional[Decimal] = None
    median: Optional[Decimal] = None
    mean: Optional[Decimal] = None
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    latest_value: Optional[Decimal] = None
    latest_timestamp: Optional[datetime] = None
    coverage_ratio: Decimal = Decimal("0.00")
    freshness_age_seconds: Optional[int] = None
    sufficiency_status: str = "INSUFFICIENT_DATA"


class ResourceTelemetryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resource_id: str
    resource_name: Optional[str] = None
    native_id: Optional[str] = None
    service_name: str
    resource_type: str
    window_days: int
    metrics: Dict[str, TelemetryMetricSummary] = Field(default_factory=dict)
    recent_observations: List[TelemetryObservationItem] = Field(default_factory=list)


class IntegrationTelemetryStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    integration_id: str
    cloudwatch_permission_status: str
    telemetry_enabled: bool
    total_resources_tracked: int
    resources_with_telemetry: int
    overall_coverage_pct: Decimal
    last_telemetry_sync: Optional[datetime] = None
    supported_namespaces: List[str] = Field(default_factory=list)


class AccountDataQualityItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: str
    account_name: str
    total_resources: int
    resources_with_telemetry: int
    telemetry_coverage_pct: Decimal
    total_observations: int


class DataQualityReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    organization_id: str
    generated_at: datetime
    total_accounts: int
    total_resources: int
    resources_with_telemetry: int
    telemetry_coverage_pct: Decimal
    total_observations: int
    accounts_quality: List[AccountDataQualityItem] = Field(default_factory=list)
    metrics_breakdown: Dict[str, int] = Field(default_factory=dict)
    data_trustworthiness_status: str
    epistemic_guarantee: str = (
        "Operational telemetry is strictly decoupled from cost calculations. Missing data is never imputed as zero."
    )
