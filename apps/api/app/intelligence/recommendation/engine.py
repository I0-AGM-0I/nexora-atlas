"""
NEXORA ATLAS - Recommendation Engine
Finalizes and validates recommendation candidates for all detected opportunities.
"""

from decimal import Decimal
from typing import List, Dict, Any
from app.intelligence.models import OpportunityCandidate, RecommendationCandidate
from app.intelligence.recommendation.rules import RecommendationRules


class RecommendationEngine:
    """Orchestrates generation, trade-off analysis, and reconciliation of recommendations."""

    @classmethod
    def process_opportunities(
        cls,
        opportunities: List[OpportunityCandidate],
        environment_by_account: Dict[str, str],
    ) -> List[OpportunityCandidate]:
        """
        Validates, normalizes, and attaches recommendation candidates to all opportunities.
        """
        processed: List[OpportunityCandidate] = []

        for opp in opportunities:
            env = environment_by_account.get(opp.account_id, "production")
            recs = RecommendationRules.generate_recommendations(opp, environment=env)
            opp.recommendations = recs
            processed.append(opp)

        return processed
