"""
NEXORA ATLAS - Intelligence Engine API Schemas
"""

from decimal import Decimal
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class RuleEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_id: str
    rule_type: str
    status: str
    skip_reason: Optional[str] = None
    findings_count: int


class IntelligenceRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: str
    organization_id: str
    ruleset_version: str
    started_at: datetime
    completed_at: datetime
    duration_ms: int
    anomalies_detected: int
    opportunities_found: int
    recommendations_generated: int
    potential_monthly_savings: Decimal
    potential_annual_savings: Decimal
    rule_evaluations: List[RuleEvaluationResponse]


class IntelligenceStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ruleset_version: str
    status: str
    last_run_at: Optional[str] = None
    last_run_id: Optional[str] = None
    active_anomalies_count: int
    active_opportunities_count: int
    addressable_monthly_savings: Decimal
    addressable_annual_savings: Decimal
    is_offline_mode: bool = True
    aws_network_disabled: bool = True
