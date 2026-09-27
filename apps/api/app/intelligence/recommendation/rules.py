"""
NEXORA ATLAS - Recommendation Strategy Rules
Generates concrete action plans for detected optimization opportunities.
"""

from decimal import Decimal
from typing import List, Dict, Any, Optional
from app.intelligence.types import WasteType, RiskLevel
from app.intelligence.models import RecommendationCandidate, OpportunityCandidate
from app.intelligence.recommendation.calculators import reconcile_savings, evaluate_recommendation_risk


class RecommendationRules:
    """Provides actionable recommendation blueprints with multiple tradeoff options where appropriate."""

    @classmethod
    def generate_recommendations(
        cls,
        opportunity: OpportunityCandidate,
        environment: str = "production",
    ) -> List[RecommendationCandidate]:
        """
        Generates or augments recommendation candidates for an opportunity.
        If the opportunity already has generated recommendations from the waste rule,
        validates and normalizes their financial reconciliation and risk ratings.
        """
        recs: List[RecommendationCandidate] = []

        if opportunity.recommendations:
            for rec in opportunity.recommendations:
                # Ensure mathematical precision reconciliation
                m_savings, a_savings = reconcile_savings(rec.estimated_monthly_savings)
                recs.append(
                    RecommendationCandidate(
                        title=rec.title,
                        category=rec.category,
                        current_configuration=rec.current_configuration,
                        recommended_configuration=rec.recommended_configuration,
                        estimated_monthly_savings=m_savings,
                        estimated_annual_savings=a_savings,
                        confidence_score=rec.confidence_score,
                        risk_level=rec.risk_level,
                        reasoning=rec.reasoning,
                        assumptions_json=rec.assumptions_json,
                        evidence_json=rec.evidence_json,
                        status=rec.status,
                    )
                )
            return recs

        # Fallback generator if an opportunity candidate had no pre-attached recommendations
        monthly_waste, annual_waste = reconcile_savings(opportunity.estimated_waste_monthly)
        risk = evaluate_recommendation_risk(
            category=opportunity.category,
            action_type=opportunity.waste_type.value,
            environment=environment,
        )

        recs.append(
            RecommendationCandidate(
                title=f"Remediate {opportunity.waste_type.value.replace('_', ' ').title()}",
                category=opportunity.category,
                current_configuration=opportunity.resource_name or "Active Cloud Resource",
                recommended_configuration="Optimized configuration per Atlas standards",
                estimated_monthly_savings=monthly_waste,
                estimated_annual_savings=annual_waste,
                confidence_score=opportunity.confidence_score,
                risk_level=risk.value,
                reasoning=f"Identified {opportunity.waste_type.value} inefficiency backed by telemetry evidence.",
                assumptions_json=opportunity.evidence_json.get("assumptions", {}),
                evidence_json=opportunity.evidence_json,
                status="OPEN",
            )
        )
        return recs
