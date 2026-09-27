"""
NEXORA ATLAS - Analytics Engine Orchestrator
Top-level coordinator executing trends, drivers, efficiency, scenarios, and portfolio analysis.
"""

from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime, timezone

from app.analytics.constants import (
    ANALYTICS_VERSION,
    SCENARIO_VERSION,
    PRICING_BASIS_SYNTHETIC,
    DEFAULT_COMPARISON_WINDOW_DAYS,
)
from app.analytics.types import ScenarioType
from app.analytics.models import (
    TrendAnalysisResult,
    DriverDecompositionResult,
    ConcentrationMetrics,
    EfficiencyReport,
    PortfolioAnalysisResult,
    ScenarioSimulationResult,
    AnalyticalExplanation,
)
from app.analytics.trends import TrendAnalyzer
from app.analytics.drivers import CostDriverAnalyzer
from app.analytics.efficiency import EfficiencyAnalyzer
from app.analytics.optimization import OptimizationPortfolio, OptimizationPlanner
from app.analytics.scenarios import ScenarioEngine


class AnalyticsEngine:
    """Coordinates advanced technology cost intelligence and optimization modeling."""

    @classmethod
    def run_full_analytics(
        cls,
        daily_records: List[Tuple[date, Decimal]],
        service_records: List[Dict[str, Any]],
        account_records: List[Dict[str, Any]],
        resource_records: List[Dict[str, Any]],
        region_records: Optional[List[Dict[str, Any]]] = None,
        resources_inventory: Optional[List[Dict[str, Any]]] = None,
        phase5_opportunities: Optional[List[Dict[str, Any]]] = None,
        phase5_recommendations: Optional[List[Dict[str, Any]]] = None,
        comparison_window_days: int = DEFAULT_COMPARISON_WINDOW_DAYS,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end analytical pipeline:
        1. Trend & Volatility Analysis
        2. Cost Driver Decomposition (Service, Account, Resource)
        3. Descriptive Concentration Metrics (HHI)
        4. Efficiency & Capacity Headroom Analysis
        5. Optimization Portfolio & Conflict Detection
        6. Scenario Simulations (Conservative, Aggressive, Modernization)
        """
        # 1. Trends
        trends = TrendAnalyzer.analyze(daily_records, comparison_window_days)

        # 2. Drivers
        drivers = CostDriverAnalyzer.decompose(
            service_records=service_records,
            account_records=account_records,
            resource_records=resource_records,
            region_records=region_records,
            comparison_window_days=comparison_window_days,
        )

        # 3. Concentration
        concentration = CostDriverAnalyzer.calculate_concentration(
            service_records=service_records,
            account_records=account_records,
            resource_records=resource_records,
        )

        # 4. Efficiency
        efficiency = EfficiencyAnalyzer.analyze(
            resources=resources_inventory or [],
            phase5_opportunities=phase5_opportunities or [],
        )

        # 5. Portfolio
        portfolio = OptimizationPortfolio.evaluate(
            opportunities=phase5_opportunities or [],
            recommendations=phase5_recommendations or [],
        )

        # 6. Scenarios
        baseline_cost = drivers.current_period_cost
        scenarios_blueprint = OptimizationPlanner.blueprint_scenarios(
            recommendations=phase5_recommendations or [],
            baseline_monthly_cost=baseline_cost,
        )

        simulated_scenarios: List[ScenarioSimulationResult] = []
        for s_type, changes in scenarios_blueprint.items():
            if changes:
                sim_res = ScenarioEngine.simulate_scenario(
                    name=f"{s_type.value.capitalize()} Optimization Plan",
                    scenario_type=s_type,
                    baseline_monthly_cost=baseline_cost,
                    proposed_changes=changes,
                    description=f"Simulated {s_type.value.lower()} infrastructure changes from active recommendations.",
                )
                simulated_scenarios.append(sim_res)

        # Progressive chain of reasoning summary
        top_driver = drivers.service_drivers[0] if drivers.service_drivers else None
        chain_summary = {
            "spend_change": str(drivers.net_change),
            "trend_direction": trends.trend_direction.value,
            "current_regime": trends.current_regime.value,
            "top_cost_driver": {
                "name": top_driver.name if top_driver else "N/A",
                "delta": str(top_driver.cost_delta) if top_driver else "0.0000",
                "absolute_contribution_pct": str(top_driver.absolute_contribution_pct) if top_driver else "0.00",
            },
            "addressable_waste": str(efficiency.estimated_addressable_waste),
            "compatible_portfolio_savings": str(portfolio.total_compatible_monthly_savings),
            "highest_portfolio_risk": portfolio.risk_profile.highest_risk,
            "provenance": {
                "analytics_version": ANALYTICS_VERSION,
                "scenario_version": SCENARIO_VERSION,
                "pricing_basis": PRICING_BASIS_SYNTHETIC,
                "calculated_at": datetime.now(timezone.utc).isoformat(),
            },
        }

        return {
            "trends": trends,
            "drivers": drivers,
            "concentration": concentration,
            "efficiency": efficiency,
            "portfolio": portfolio,
            "scenarios": simulated_scenarios,
            "chain_summary": chain_summary,
        }
