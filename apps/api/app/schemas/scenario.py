"""
NEXORA ATLAS - Scenario Workbench API Schemas
"""

from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class ScenarioChangeItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    scenario_id: str
    resource_id: Optional[str] = None
    change_type: str
    current_spec: str
    proposed_spec: str
    delta_cost: Decimal


class ScenarioItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    baseline_monthly_cost: Decimal
    projected_monthly_cost: Decimal
    monthly_savings: Decimal
    percentage_savings: Decimal
    performance_risk: str
    reliability_risk: str
    complexity_level: str
    assumptions_json: Optional[Dict[str, Any]] = None
    changes: List[ScenarioChangeItem] = []


class ScenarioListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scenarios: List[ScenarioItem]


class ScenarioSimulationRequest(BaseModel):
    name: str = "Custom What-If Scenario"
    scenario_type: str = "CUSTOM"
    description: Optional[str] = None
    baseline_monthly_cost: Optional[Decimal] = None
    proposed_changes: List[Dict[str, Any]]
    custom_assumptions: Optional[Dict[str, Any]] = None
