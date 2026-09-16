"""
NEXORA ATLAS - Forecast Engine (Boundary)
Phase 1 Module Boundary: Statistical forecasting deferred to Phase 9.
"""

from typing import Any, Dict, List


class ForecastEngine:
    """Architectural interface for statistical cost forecasting and confidence intervals."""

    def generate_forecast(
        self,
        account_id: str,
        horizon_months: int = 3,
    ) -> List[Dict[str, Any]]:
        """Projects future spend using transparent statistical time-series models."""
        raise NotImplementedError("ForecastEngine implementation scheduled for Phase 9.")
