"""
NEXORA ATLAS - Telemetry Schemas
Establishes the architectural separation between Financial Cost Data and Operational Telemetry.
"""

from datetime import date, datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class CostDataRecord(BaseModel):
    """Financial billing telemetry (e.g. AWS Cost Explorer, CUR)."""
    model_config = ConfigDict(from_attributes=True)

    account_id: str
    service_name: str
    usage_date: date
    unblended_cost: float
    amortized_cost: float
    usage_quantity: float
    usage_unit: str
    currency: str = "INR"
    resource_id: Optional[str] = None


class OperationalTelemetryRecord(BaseModel):
    """System performance telemetry (e.g. CloudWatch, Datadog, Prometheus)."""
    model_config = ConfigDict(from_attributes=True)

    resource_id: str
    timestamp: datetime
    metric_name: str = Field(..., description="e.g. CPUUtilization, MemoryUtilization, NetworkIn")
    p50: float
    p95: float
    maximum: float
    sample_window_minutes: int
    dimensions: Optional[Dict[str, Any]] = None
