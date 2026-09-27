"""
NEXORA ATLAS - Cost Driver & Spend Concentration Analyzer
Orchestrates multi-dimensional attribution and calculates descriptive spend concentration metrics.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Tuple, Optional

from app.analytics.constants import ANALYTICS_VERSION, DEFAULT_COMPARISON_WINDOW_DAYS
from app.analytics.types import DriverDimension, SufficiencyStatus
from app.analytics.models import (
    DriverDecompositionResult,
    ConcentrationMetrics,
    AnalyticalExplanation,
)
from app.analytics.drivers.attribution import attribute_dimension_drivers


class CostDriverAnalyzer:
    """Orchestrates period-over-period cost attribution and spend concentration."""

    @classmethod
    def decompose(
        cls,
        service_records: List[Dict[str, Any]],
        account_records: List[Dict[str, Any]],
        resource_records: List[Dict[str, Any]],
        region_records: Optional[List[Dict[str, Any]]] = None,
        comparison_window_days: int = DEFAULT_COMPARISON_WINDOW_DAYS,
    ) -> DriverDecompositionResult:
        """
        Decomposes period-over-period spend change across Service, Account, Resource, and Region dimensions.
        Validates financial invariant: sum(deltas) == net_change.
        """
        if not service_records and not account_records:
            return DriverDecompositionResult(
                sufficiency_status=SufficiencyStatus.INSUFFICIENT_DATA,
                comparison_window_days=comparison_window_days,
                current_period_cost=Decimal("0.0000"),
                previous_period_cost=Decimal("0.0000"),
                net_change=Decimal("0.0000"),
                net_change_pct=Decimal("0.00"),
                service_drivers=[],
                account_drivers=[],
                resource_drivers=[],
                region_drivers=[],
                reconciled=True,
                explanation=AnalyticalExplanation(
                    observations={},
                    derived_metrics={},
                    classification="INSUFFICIENT_DATA",
                    evidence=["No cost records available for the requested comparison window."],
                    method="period_delta_decomposition_v1",
                    parameters={"comparison_window_days": comparison_window_days},
                    version=ANALYTICS_VERSION,
                ),
            )

        # Baseline sums
        current_total = sum((r["current_cost"] for r in service_records), Decimal("0.0000")).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        previous_total = sum((r["previous_cost"] for r in service_records), Decimal("0.0000")).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        net_change = (current_total - previous_total).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        if previous_total > Decimal("0"):
            net_change_pct = ((net_change / previous_total) * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            net_change_pct = Decimal("0.00")

        # Decompose across dimensions
        service_drivers = attribute_dimension_drivers(
            DriverDimension.SERVICE, service_records, net_change, comparison_window_days
        )
        account_drivers = attribute_dimension_drivers(
            DriverDimension.ACCOUNT, account_records, net_change, comparison_window_days
        )
        resource_drivers = attribute_dimension_drivers(
            DriverDimension.RESOURCE, resource_records, net_change, comparison_window_days
        )
        region_drivers = attribute_dimension_drivers(
            DriverDimension.REGION, region_records or [], net_change, comparison_window_days
        )

        # Invariant checks:
        # sum(service_deltas) == net_change
        service_delta_sum = sum((d.cost_delta for d in service_drivers), Decimal("0.0000"))
        account_delta_sum = sum((d.cost_delta for d in account_drivers), Decimal("0.0000"))
        is_reconciled = (service_delta_sum == net_change) and (account_delta_sum == net_change)

        explanation = AnalyticalExplanation(
            observations={
                "current_total_spend": str(current_total),
                "previous_total_spend": str(previous_total),
                "services_count": len(service_records),
                "accounts_count": len(account_records),
                "resources_count": len(resource_records),
            },
            derived_metrics={
                "net_change": str(net_change),
                "net_change_pct": str(net_change_pct),
                "service_delta_sum": str(service_delta_sum),
                "account_delta_sum": str(account_delta_sum),
                "reconciliation_verified": is_reconciled,
            },
            classification="RECONCILED" if is_reconciled else "DISCREPANCY_DETECTED",
            evidence=[
                f"Total spend changed from ₹{previous_total} to ₹{current_total} (Net: ₹{net_change})",
                f"Service deltas sum to ₹{service_delta_sum} (Matches total: {service_delta_sum == net_change})",
                f"Account deltas sum to ₹{account_delta_sum} (Matches total: {account_delta_sum == net_change})",
            ],
            method="period_delta_decomposition_v1",
            parameters={"comparison_window_days": comparison_window_days},
            version=ANALYTICS_VERSION,
        )

        return DriverDecompositionResult(
            sufficiency_status=SufficiencyStatus.AVAILABLE,
            comparison_window_days=comparison_window_days,
            current_period_cost=current_total,
            previous_period_cost=previous_total,
            net_change=net_change,
            net_change_pct=net_change_pct,
            service_drivers=service_drivers,
            account_drivers=account_drivers,
            resource_drivers=resource_drivers,
            region_drivers=region_drivers,
            reconciled=is_reconciled,
            explanation=explanation,
        )

    @classmethod
    def calculate_concentration(
        cls,
        service_records: List[Dict[str, Any]],
        account_records: List[Dict[str, Any]],
        resource_records: List[Dict[str, Any]],
    ) -> ConcentrationMetrics:
        """
        Calculates descriptive spend concentration metrics:
        - Top 1 service share %
        - Top 3 service share %
        - Top 5 resource share %
        - Top account share %
        - Spend Concentration Index (HHI) = sum(share_i^2)
        Note: HHI is descriptive only; it is not an optimization score.
        """
        total_service_spend = sum((r["current_cost"] for r in service_records), Decimal("0.0000"))

        if total_service_spend <= Decimal("0"):
            return ConcentrationMetrics(
                sufficiency_status=SufficiencyStatus.INSUFFICIENT_DATA,
                top_1_service_share_pct=Decimal("0.00"),
                top_3_service_share_pct=Decimal("0.00"),
                top_5_resource_share_pct=Decimal("0.00"),
                top_account_share_pct=Decimal("0.00"),
                spend_concentration_index=Decimal("0.00"),
                hhi_interpretation="No spend recorded",
                explanation=AnalyticalExplanation(
                    observations={"total_spend": "0.0000"},
                    derived_metrics={},
                    classification="INSUFFICIENT_DATA",
                    evidence=["Zero total spend observed in the evaluation window."],
                    method="hhi_descriptive_v1",
                    version=ANALYTICS_VERSION,
                ),
            )

        # Service shares
        sorted_services = sorted(service_records, key=lambda x: x["current_cost"], reverse=True)
        top_1_service_share = (
            ((sorted_services[0]["current_cost"] / total_service_spend) * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if sorted_services
            else Decimal("0.00")
        )

        top_3_sum = sum((s["current_cost"] for s in sorted_services[:3]), Decimal("0.0000"))
        top_3_service_share = ((top_3_sum / total_service_spend) * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Account share
        total_account_spend = sum((r["current_cost"] for r in account_records), Decimal("0.0000"))
        sorted_accounts = sorted(account_records, key=lambda x: x["current_cost"], reverse=True)
        top_account_share = (
            ((sorted_accounts[0]["current_cost"] / total_account_spend) * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if sorted_accounts and total_account_spend > Decimal("0")
            else Decimal("0.00")
        )

        # Resource share
        total_resource_spend = sum((r["current_cost"] for r in resource_records), Decimal("0.0000"))
        sorted_resources = sorted(resource_records, key=lambda x: x["current_cost"], reverse=True)
        top_5_resource_sum = sum((r["current_cost"] for r in sorted_resources[:5]), Decimal("0.0000"))
        top_5_resource_share = (
            ((top_5_resource_sum / total_resource_spend) * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if sorted_resources and total_resource_spend > Decimal("0")
            else Decimal("0.00")
        )

        # Descriptive HHI calculation on service shares:
        # HHI = sum((share_pct)^2), range 0 to 10,000
        hhi = Decimal("0.00")
        for s in sorted_services:
            share_pct = (s["current_cost"] / total_service_spend) * Decimal("100")
            hhi += share_pct**2
        hhi = hhi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        if hhi >= Decimal("2500"):
            hhi_interpretation = "Highly Concentrated (Single/few services dominate portfolio spend)"
        elif hhi >= Decimal("1500"):
            hhi_interpretation = "Moderately Concentrated"
        else:
            hhi_interpretation = "Diversified (Spend evenly distributed across services)"

        explanation = AnalyticalExplanation(
            observations={
                "total_spend": str(total_service_spend),
                "top_service": sorted_services[0]["name"] if sorted_services else "None",
            },
            derived_metrics={
                "top_1_service_share_pct": str(top_1_service_share),
                "top_3_service_share_pct": str(top_3_service_share),
                "top_5_resource_share_pct": str(top_5_resource_share),
                "top_account_share_pct": str(top_account_share),
                "spend_concentration_index": str(hhi),
            },
            classification="DESCRIPTIVE_CONCENTRATION",
            evidence=[
                f"Top service accounts for {top_1_service_share}% of total spend",
                f"Top 3 services account for {top_3_service_share}% of total spend",
                f"Descriptive HHI is {hhi} ({hhi_interpretation})",
            ],
            method="hhi_descriptive_v1",
            version=ANALYTICS_VERSION,
        )

        return ConcentrationMetrics(
            sufficiency_status=SufficiencyStatus.AVAILABLE,
            top_1_service_share_pct=top_1_service_share,
            top_3_service_share_pct=top_3_service_share,
            top_5_resource_share_pct=top_5_resource_share,
            top_account_share_pct=top_account_share,
            spend_concentration_index=hhi,
            hhi_interpretation=hhi_interpretation,
            explanation=explanation,
        )
