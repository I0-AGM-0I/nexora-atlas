"""
NEXORA ATLAS - Advanced Analytics Domain Models & Schemas
Pydantic contracts for deterministic trends, drivers, efficiency, scenarios, and portfolio.
"""

from decimal import Decimal
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict

from app.analytics.constants import ANALYTICS_VERSION, SCENARIO_VERSION, PRICING_BASIS_SYNTHETIC
from app.analytics.types import (
    DataCategory,
    SufficiencyStatus,
    TrendDirection,
    CostRegime,
    DriverDimension,
    ChangeClassification,
    DependencyType,
    ComplexityLevel,
    ReversibilityLevel,
    ScenarioType,
)


class AnalyticalExplanation(BaseModel):
    """Machine-readable structured explanation of analytical provenance."""
    model_config = ConfigDict(extra="ignore")

    observations: Dict[str, Any] = Field(default_factory=dict, description="Directly measured values")
    derived_metrics: Dict[str, Any] = Field(default_factory=dict, description="Mathematically computed metrics")
    classification: Optional[str] = Field(None, description="Deterministic rule-based inference or regime")
    evidence: List[str] = Field(default_factory=list, description="Explicit reasons and supporting facts")
    method: str = Field(description="Analytical algorithm or calculation procedure")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Window sizes, thresholds, coefficients")
    assumptions: Dict[str, Any] = Field(default_factory=dict, description="Explicit scenario or calculation assumptions")
    version: str = ANALYTICS_VERSION


class DailyTrendPoint(BaseModel):
    """Daily cost observation with rolling metrics and regime tag."""
    model_config = ConfigDict(extra="ignore")

    date: str
    observed_cost: Decimal
    rolling_mean_7d: Optional[Decimal] = None
    rolling_mean_14d: Optional[Decimal] = None
    rolling_mean_30d: Optional[Decimal] = None
    regime: CostRegime


class TrendAnalysisResult(BaseModel):
    """Deterministic trend and volatility analysis result."""
    model_config = ConfigDict(extra="ignore")

    sufficiency_status: SufficiencyStatus
    trend_direction: TrendDirection
    current_regime: CostRegime
    mean_daily_spend: Decimal
    stddev_daily_spend: Decimal
    coefficient_of_variation: Decimal
    max_daily_deviation: Decimal
    period_over_period_delta: Decimal
    period_over_period_pct: Decimal
    daily_series: List[DailyTrendPoint] = Field(default_factory=list)
    explanation: AnalyticalExplanation


class CostDriverItem(BaseModel):
    """Individual driver of period-over-period spend change."""
    model_config = ConfigDict(extra="ignore")

    dimension: DriverDimension
    identifier: str
    name: str
    current_period_cost: Decimal
    previous_period_cost: Decimal
    cost_delta: Decimal
    absolute_contribution_pct: Decimal
    net_change_contribution_pct: Optional[Decimal] = None
    direction: str
    rank: int
    classification: ChangeClassification
    explanation: AnalyticalExplanation


class DriverDecompositionResult(BaseModel):
    """Multi-dimensional period-over-period change decomposition."""
    model_config = ConfigDict(extra="ignore")

    sufficiency_status: SufficiencyStatus
    comparison_window_days: int
    current_period_cost: Decimal
    previous_period_cost: Decimal
    net_change: Decimal
    net_change_pct: Decimal
    service_drivers: List[CostDriverItem] = Field(default_factory=list)
    account_drivers: List[CostDriverItem] = Field(default_factory=list)
    resource_drivers: List[CostDriverItem] = Field(default_factory=list)
    region_drivers: List[CostDriverItem] = Field(default_factory=list)
    reconciled: bool = True
    explanation: AnalyticalExplanation


class ConcentrationMetrics(BaseModel):
    """Descriptive spend concentration metrics (Top-N and descriptive HHI)."""
    model_config = ConfigDict(extra="ignore")

    sufficiency_status: SufficiencyStatus
    top_1_service_share_pct: Decimal
    top_3_service_share_pct: Decimal
    top_5_resource_share_pct: Decimal
    top_account_share_pct: Decimal
    spend_concentration_index: Decimal
    hhi_interpretation: str
    explanation: AnalyticalExplanation


class HeadroomItem(BaseModel):
    """Observed capacity headroom for compute/database resources."""
    model_config = ConfigDict(extra="ignore")

    resource_id: str
    resource_name: str
    service_name: str
    instance_type: Optional[str] = None
    p95_utilization_cpu: Optional[Decimal] = None
    p95_utilization_memory: Optional[Decimal] = None
    observed_utilization_headroom_cpu: Optional[Decimal] = None
    observed_utilization_headroom_memory: Optional[Decimal] = None
    sufficiency_status: SufficiencyStatus


class UnitEconomicsContract(BaseModel):
    """Unit economics metric contract (unconfigured in demo mode, zero fake metrics)."""
    model_config = ConfigDict(extra="ignore")

    metric_name: str
    unit_name: str
    status: SufficiencyStatus = SufficiencyStatus.NOT_CONFIGURED
    cost_per_unit: Optional[Decimal] = None
    explanation: str


class EfficiencyReport(BaseModel):
    """Resource efficiency and capacity headroom report."""
    model_config = ConfigDict(extra="ignore")

    sufficiency_status: SufficiencyStatus
    headroom_items: List[HeadroomItem] = Field(default_factory=list)
    idle_resources_count: int
    idle_resources_cost: Decimal
    estimated_addressable_waste: Decimal
    unit_economics: List[UnitEconomicsContract] = Field(default_factory=list)
    explanation: AnalyticalExplanation


class ScenarioConstraintViolation(BaseModel):
    """Explicit violation detected during scenario validation."""
    model_config = ConfigDict(extra="ignore")

    rule_name: str
    resource_id: Optional[str] = None
    reason: str
    severity: str = "ERROR"


class ScenarioChangeCalculation(BaseModel):
    """Itemized infrastructure modification within a scenario."""
    model_config = ConfigDict(extra="ignore")

    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    change_type: str
    current_spec: str
    proposed_spec: str
    current_monthly_cost: Decimal
    projected_monthly_cost: Decimal
    delta_cost: Decimal
    risk_level: str
    complexity_level: str
    assumptions: Dict[str, Any] = Field(default_factory=dict)


class ScenarioSimulationResult(BaseModel):
    """Simulation of a what-if architecture scenario."""
    model_config = ConfigDict(extra="ignore")

    scenario_id: Optional[str] = None
    name: str
    scenario_type: ScenarioType
    description: Optional[str] = None
    baseline_monthly_cost: Decimal
    projected_monthly_cost: Decimal
    monthly_savings: Decimal
    annual_savings: Decimal
    percentage_savings: Decimal
    performance_risk: str
    reliability_risk: str
    complexity_level: str
    assumptions: Dict[str, Any] = Field(default_factory=dict)
    changes: List[ScenarioChangeCalculation] = Field(default_factory=list)
    violations: List[ScenarioConstraintViolation] = Field(default_factory=list)
    is_valid: bool = True
    explanation: AnalyticalExplanation


class PortfolioRiskProfile(BaseModel):
    """Descriptive breakdown of portfolio risk (no magic score)."""
    model_config = ConfigDict(extra="ignore")

    highest_risk: str
    count_low: int
    count_medium: int
    count_high: int


class RecommendationConflict(BaseModel):
    """Detected conflict between mutually exclusive recommendations."""
    model_config = ConfigDict(extra="ignore")

    resource_id: str
    resource_name: Optional[str] = None
    recommendation_ids: List[str]
    titles: List[str]
    reason: str


class RecommendationDependency(BaseModel):
    """Declared prerequisite relationship between recommendations."""
    model_config = ConfigDict(extra="ignore")

    dependent_recommendation_id: str
    prerequisite_recommendation_id: str
    dependency_type: DependencyType
    reason: str


class PortfolioAnalysisResult(BaseModel):
    """Collective portfolio evaluation of optimization opportunities and recommendations."""
    model_config = ConfigDict(extra="ignore")

    total_opportunities_count: int
    total_recommendations_count: int
    conflicts: List[RecommendationConflict] = Field(default_factory=list)
    dependencies: List[RecommendationDependency] = Field(default_factory=list)
    compatible_recommendations_count: int
    total_compatible_monthly_savings: Decimal
    total_compatible_annual_savings: Decimal
    risk_profile: PortfolioRiskProfile
    complexity_breakdown: Dict[str, int] = Field(default_factory=dict)
    reversibility_breakdown: Dict[str, int] = Field(default_factory=dict)
    explanation: AnalyticalExplanation
