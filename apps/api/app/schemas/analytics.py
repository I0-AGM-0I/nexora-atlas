"""
NEXORA ATLAS - Analytics API Schemas
Pydantic schemas for /api/v1/analytics endpoints.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

from app.analytics.models import (
    TrendAnalysisResult,
    DriverDecompositionResult,
    ConcentrationMetrics,
    EfficiencyReport,
    PortfolioAnalysisResult,
    ScenarioSimulationResult,
)


class AnalyticsTrendsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    trends: TrendAnalysisResult


class AnalyticsDriversResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    drivers: DriverDecompositionResult


class AnalyticsConcentrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    concentration: ConcentrationMetrics


class AnalyticsEfficiencyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    efficiency: EfficiencyReport


class AnalyticsPortfolioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    portfolio: PortfolioAnalysisResult


class AnalyticsSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    trends: TrendAnalysisResult
    drivers: DriverDecompositionResult
    concentration: ConcentrationMetrics
    efficiency: EfficiencyReport
    portfolio: PortfolioAnalysisResult
    scenarios: List[ScenarioSimulationResult]
    chain_summary: Dict[str, Any]
