"""
NEXORA ATLAS - Anomaly API Schemas
Preserves structural separation between Observed Facts and Algorithmic Inferences.
"""

from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class AnomalyObservedFacts(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    observed_cost: Decimal
    baseline_cost: Decimal
    percentage_change: Decimal
    detected_at: str
    detection_rule: str
    observed_metrics_json: Optional[Dict[str, Any]] = None


class AnomalyInferredAnalysis(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    severity: str
    status: str
    inferred_cause: Optional[str] = None
    confidence_pct: Decimal
    inference_details_json: Optional[Dict[str, Any]] = None


class AnomalyItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    account_name: str
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    resource_native_id: Optional[str] = None
    service_name: str
    observed: AnomalyObservedFacts
    inference: AnomalyInferredAnalysis


class AnomalyListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: List[AnomalyItem]
    total_count: int
    open_count: int
