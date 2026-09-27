"""
NEXORA ATLAS - Optimization Opportunity & Recommendation API Schemas
"""

from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class RecommendationItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str
    title: str
    category: str
    current_configuration: str
    recommended_configuration: str
    estimated_monthly_savings: Decimal
    estimated_annual_savings: Decimal
    confidence_pct: Decimal
    risk_level: str
    reasoning: str


class OpportunityItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    account_name: str
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    resource_native_id: Optional[str] = None
    category: str
    waste_type: str
    severity: str
    status: str
    estimated_waste_monthly: Decimal
    estimated_waste_annual: Decimal
    evidence_json: Dict[str, Any]
    recommendations: List[RecommendationItem] = []


class OptimizationOverviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    potential_monthly_savings: Decimal
    potential_annual_savings: Decimal
    opportunity_count: int
    recommendation_count: int
    opportunities: List[OpportunityItem]
