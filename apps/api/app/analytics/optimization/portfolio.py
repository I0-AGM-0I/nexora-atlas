"""
NEXORA ATLAS - Optimization Portfolio & Conflict Detection
Evaluates collective recommendations, detects conflicts, maps dependencies, and reports descriptive risk.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Tuple
from collections import defaultdict

from app.analytics.constants import ANALYTICS_VERSION
from app.analytics.types import DependencyType, ComplexityLevel, ReversibilityLevel
from app.analytics.models import (
    RecommendationConflict,
    RecommendationDependency,
    PortfolioRiskProfile,
    PortfolioAnalysisResult,
    AnalyticalExplanation,
)
from app.analytics.optimization.prioritization import assess_recommendation_tradeoffs


class OptimizationPortfolio:
    """Evaluates optimization recommendations collectively across an infrastructure estate."""

    @classmethod
    def evaluate(
        cls,
        opportunities: List[Dict[str, Any]],
        recommendations: List[Dict[str, Any]],
    ) -> PortfolioAnalysisResult:
        """
        Evaluates the complete recommendation portfolio:
        - Detects mutually exclusive conflicts on shared resources.
        - Maps required dependencies and recommended precautions.
        - Calculates total compatible monthly & annual savings (zero double-counting).
        - Generates descriptive risk profile (Correction 9: NO composite magic score).
        """
        conflicts: List[RecommendationConflict] = []
        dependencies: List[RecommendationDependency] = []

        # Group recommendations by resource_id to detect conflicts
        resource_recs: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for r in recommendations:
            res_id = str(r.get("resource_id", ""))
            if res_id:
                resource_recs[res_id].append(r)

        conflicting_rec_ids = set()
        for res_id, recs in resource_recs.items():
            if len(recs) > 1:
                # Multiple recommendations on the same resource conflict
                rec_ids = [str(x.get("id")) for x in recs]
                titles = [str(x.get("title")) for x in recs]
                conflicts.append(
                    RecommendationConflict(
                        resource_id=res_id,
                        resource_name=str(recs[0].get("resource_name") or recs[0].get("title")),
                        recommendation_ids=rec_ids,
                        titles=titles,
                        reason="Mutually exclusive recommendations targeting the same infrastructure resource.",
                    )
                )
                # Flag secondary candidates as conflicting
                # Keep the first candidate (e.g. Conservative) as active in the compatible portfolio
                for secondary in recs[1:]:
                    conflicting_rec_ids.add(str(secondary.get("id")))

        # Map domain dependencies
        for r in recommendations:
            rec_id = str(r.get("id"))
            title = str(r.get("title", "")).lower()
            rec_config = str(r.get("recommended_configuration", "")).lower()

            # EBS deletion dependency: snapshot precaution
            if "unattached" in title and ("ebs" in title or "volume" in title):
                dependencies.append(
                    RecommendationDependency(
                        dependent_recommendation_id=rec_id,
                        prerequisite_recommendation_id=f"snapshot-precaution-{rec_id}",
                        dependency_type=DependencyType.RECOMMENDED_PRECAUTION,
                        reason="Verify EBS volume snapshot hygiene before permanent volume termination.",
                    )
                )

            # Graviton modernization: architecture compatibility testing
            if "graviton" in rec_config or "arm" in rec_config or "c7g" in rec_config:
                dependencies.append(
                    RecommendationDependency(
                        dependent_recommendation_id=rec_id,
                        prerequisite_recommendation_id=f"arm-test-compat-{rec_id}",
                        dependency_type=DependencyType.REQUIRED_DEPENDENCY,
                        reason="Workload binary compatibility verification required before deploying ARM Graviton.",
                    )
                )

        # Calculate compatible portfolio metrics (excluding secondary conflicting recs)
        compatible_recs = [r for r in recommendations if str(r.get("id")) not in conflicting_rec_ids]
        total_compatible_monthly = sum(
            (Decimal(str(r.get("estimated_monthly_savings", "0.0000"))) for r in compatible_recs),
            Decimal("0.0000"),
        ).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        total_compatible_annual = (total_compatible_monthly * Decimal("12")).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )

        # Descriptive risk breakdown (Correction 9)
        count_low = 0
        count_medium = 0
        count_high = 0
        complexity_counts: Dict[str, int] = defaultdict(int)
        reversibility_counts: Dict[str, int] = defaultdict(int)

        for r in compatible_recs:
            risk = str(r.get("risk_level", "LOW")).upper()
            if risk == "HIGH" or risk == "CRITICAL":
                count_high += 1
            elif risk == "MEDIUM":
                count_medium += 1
            else:
                count_low += 1

            tradeoffs = assess_recommendation_tradeoffs(
                category=str(r.get("category", "")),
                action_type=str(r.get("title", "")),
                risk_level=risk,
                estimated_monthly_savings=Decimal(str(r.get("estimated_monthly_savings", "0.0000"))),
                confidence_score=Decimal(str(r.get("confidence_pct", "90.00"))),
            )
            complexity_counts[tradeoffs["complexity_level"]] += 1
            reversibility_counts[tradeoffs["reversibility_level"]] += 1

        if count_high > 0:
            highest_risk = "HIGH"
        elif count_medium > 0:
            highest_risk = "MEDIUM"
        else:
            highest_risk = "LOW"

        risk_profile = PortfolioRiskProfile(
            highest_risk=highest_risk,
            count_low=count_low,
            count_medium=count_medium,
            count_high=count_high,
        )

        explanation = AnalyticalExplanation(
            observations={
                "total_opportunities": len(opportunities),
                "total_recommendations": len(recommendations),
                "compatible_recommendations": len(compatible_recs),
                "conflicts_count": len(conflicts),
                "dependencies_count": len(dependencies),
            },
            derived_metrics={
                "compatible_monthly_savings": str(total_compatible_monthly),
                "compatible_annual_savings": str(total_compatible_annual),
                "highest_risk": highest_risk,
            },
            classification="PORTFOLIO_ANALYSIS",
            evidence=[
                f"Identified {len(conflicts)} conflicting recommendation pairs targeting identical resources",
                f"Resolved compatible portfolio of {len(compatible_recs)} non-conflicting actions",
                f"Total compatible addressable savings: ₹{total_compatible_monthly}/month (₹{total_compatible_annual}/year)",
                f"Descriptive risk profile: {count_low} Low, {count_medium} Medium, {count_high} High (Zero magic score)",
            ],
            method="portfolio_conflict_resolution_v1",
            version=ANALYTICS_VERSION,
        )

        return PortfolioAnalysisResult(
            total_opportunities_count=len(opportunities),
            total_recommendations_count=len(recommendations),
            conflicts=conflicts,
            dependencies=dependencies,
            compatible_recommendations_count=len(compatible_recs),
            total_compatible_monthly_savings=total_compatible_monthly,
            total_compatible_annual_savings=total_compatible_annual,
            risk_profile=risk_profile,
            complexity_breakdown=dict(complexity_counts),
            reversibility_breakdown=dict(reversibility_counts),
            explanation=explanation,
        )
