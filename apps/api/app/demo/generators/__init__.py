"""
NEXORA ATLAS - Demo Generators Package
"""

from app.demo.generators.costs import generate_cost_history
from app.demo.generators.anomalies import generate_anomalies
from app.demo.generators.opportunities import generate_opportunities_and_recommendations
from app.demo.generators.scenarios import generate_scenarios
from app.demo.generators.forecasts import generate_forecasts

__all__ = [
    "generate_cost_history",
    "generate_anomalies",
    "generate_opportunities_and_recommendations",
    "generate_scenarios",
    "generate_forecasts",
]
