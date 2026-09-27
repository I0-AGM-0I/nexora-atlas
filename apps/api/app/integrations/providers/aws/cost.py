"""
NEXORA ATLAS - AWS Cost Explorer Ingestion Adapter
Implements dual-path billing data retrieval:
1. get_aggregated_costs: 90-day historical trend via GetCostAndUsage (Service/Account/Region).
2. get_resource_costs: 14-day recent window via GetCostAndUsageWithResources.
Enforces deterministic SHA-256 source_record_key and prevents heterogeneous UsageQuantity summing.
"""

import hashlib
import logging
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional, Tuple
from botocore.exceptions import ClientError

from app.integrations.providers.base import (
    DiscoveredCostRecord,
    CostAttributionLevel,
)
from app.integrations.providers.aws.client import AWSClientFactory

logger = logging.getLogger("atlas.aws.cost")


class AWSCostExplorerAdapter:
    """Read-only adapter for AWS Cost Explorer."""

    def __init__(self, client_factory: AWSClientFactory):
        self.client_factory = client_factory

    @staticmethod
    def _generate_source_record_key(
        account_id: str,
        usage_date: date,
        service_name: str,
        resource_id: Optional[str],
        region: Optional[str],
        usage_type: Optional[str],
        operation: Optional[str],
        usage_unit: Optional[str],
        attribution_level: CostAttributionLevel,
    ) -> str:
        """
        Computes deterministic SHA-256 identity key for a billing record.
        Ensures robust idempotency across repeated and incremental synchronizations.
        """
        canonical_str = (
            f"{account_id}|{usage_date.isoformat()}|{service_name}|"
            f"{resource_id or ''}|{region or ''}|{usage_type or ''}|"
            f"{operation or ''}|{usage_unit or ''}|{attribution_level.value}"
        )
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def get_aggregated_costs(
        self,
        account_id: str,
        start_date: date,
        end_date: date,
    ) -> List[DiscoveredCostRecord]:
        """
        Queries service- and account-level aggregated costs over up to 90 days.
        Uses ce:GetCostAndUsage with daily granularity.
        """
        ce_client = self.client_factory.get_client("ce", region="us-east-1")
        records: List[DiscoveredCostRecord] = []
        next_token = None

        logger.info(
            "Querying aggregated Cost Explorer spend for account %s from %s to %s",
            account_id,
            start_date,
            end_date,
        )

        while True:
            kwargs: Dict[str, Any] = {
                "TimePeriod": {
                    "Start": start_date.isoformat(),
                    "End": end_date.isoformat(),
                },
                "Granularity": "DAILY",
                "Metrics": ["UnblendedCost", "AmortizedCost", "UsageQuantity"],
                "GroupBy": [
                    {"Type": "DIMENSION", "Key": "SERVICE"},
                    {"Type": "DIMENSION", "Key": "USAGE_TYPE"},
                ],
            }
            if next_token:
                kwargs["NextPageToken"] = next_token

            def _call():
                return ce_client.get_cost_and_usage(**kwargs)

            response = AWSClientFactory.execute_with_retry("GetCostAndUsage", _call)

            for time_period in response.get("ResultsByTime", []):
                period_date_str = time_period.get("TimePeriod", {}).get("Start")
                if not period_date_str:
                    continue
                period_date = date.fromisoformat(period_date_str)

                for group in time_period.get("Groups", []):
                    keys = group.get("Keys", [])
                    service_name = keys[0] if len(keys) > 0 else "Unknown"
                    usage_type = keys[1] if len(keys) > 1 else None

                    metrics = group.get("Metrics", {})
                    unblended_raw = metrics.get("UnblendedCost", {}).get("Amount", "0.0")
                    amortized_raw = metrics.get("AmortizedCost", {}).get("Amount", "0.0")
                    currency = metrics.get("UnblendedCost", {}).get("Unit", "USD")

                    # Handle usage quantity safely
                    usage_metric = metrics.get("UsageQuantity", {})
                    qty_raw = usage_metric.get("Amount")
                    qty_unit = usage_metric.get("Unit")

                    unblended_cost = Decimal(str(unblended_raw)).quantize(
                        Decimal("0.0001"), rounding=ROUND_HALF_UP
                    )
                    amortized_cost = Decimal(str(amortized_raw)).quantize(
                        Decimal("0.0001"), rounding=ROUND_HALF_UP
                    )
                    usage_quantity = None
                    if qty_raw is not None:
                        try:
                            usage_quantity = Decimal(str(qty_raw)).quantize(
                                Decimal("0.0001"), rounding=ROUND_HALF_UP
                            )
                        except Exception:
                            pass

                    # Skip zero or negative noise records if both costs are exactly 0
                    if unblended_cost == Decimal("0.0000") and amortized_cost == Decimal("0.0000"):
                        continue

                    source_key = self._generate_source_record_key(
                        account_id=account_id,
                        usage_date=period_date,
                        service_name=service_name,
                        resource_id=None,
                        region=None,
                        usage_type=usage_type,
                        operation=None,
                        usage_unit=qty_unit,
                        attribution_level=CostAttributionLevel.SERVICE,
                    )

                    records.append(
                        DiscoveredCostRecord(
                            usage_date=period_date,
                            service_name=service_name,
                            unblended_cost=unblended_cost,
                            amortized_cost=amortized_cost,
                            usage_quantity=usage_quantity,
                            usage_unit=qty_unit,
                            usage_type=usage_type,
                            operation=None,
                            currency=currency,
                            resource_native_id=None,
                            attribution_level=CostAttributionLevel.SERVICE,
                            source_record_key=source_key,
                        )
                    )

            next_token = response.get("NextPageToken")
            if not next_token:
                break

        return records

    def get_resource_costs(
        self,
        account_id: str,
        start_date: date,
        end_date: date,
    ) -> Tuple[List[DiscoveredCostRecord], bool, Optional[str]]:
        """
        Queries resource-level attributed costs for a recent window (max 14 days).
        Uses ce:GetCostAndUsageWithResources (opt-in capability).
        Returns: (records, is_available, failure_reason)
        """
        # AWS documentation imposes strict 14-day limit on GetCostAndUsageWithResources
        max_allowed_start = end_date - timedelta(days=14)
        effective_start = max(start_date, max_allowed_start)

        ce_client = self.client_factory.get_client("ce", region="us-east-1")
        records: List[DiscoveredCostRecord] = []
        next_token = None

        logger.info(
            "Querying resource-level Cost Explorer spend for account %s from %s to %s",
            account_id,
            effective_start,
            end_date,
        )

        try:
            while True:
                kwargs: Dict[str, Any] = {
                    "TimePeriod": {
                        "Start": effective_start.isoformat(),
                        "End": end_date.isoformat(),
                    },
                    "Granularity": "DAILY",
                    "Metrics": ["UnblendedCost", "AmortizedCost"],
                    "GroupBy": [
                        {"Type": "DIMENSION", "Key": "SERVICE"},
                        {"Type": "DIMENSION", "Key": "RESOURCE_ID"},
                    ],
                }
                if next_token:
                    kwargs["NextPageToken"] = next_token

                def _call():
                    return ce_client.get_cost_and_usage_with_resources(**kwargs)

                response = AWSClientFactory.execute_with_retry(
                    "GetCostAndUsageWithResources", _call
                )

                for time_period in response.get("ResultsByTime", []):
                    period_date_str = time_period.get("TimePeriod", {}).get("Start")
                    if not period_date_str:
                        continue
                    period_date = date.fromisoformat(period_date_str)

                    for group in time_period.get("Groups", []):
                        keys = group.get("Keys", [])
                        service_name = keys[0] if len(keys) > 0 else "Unknown"
                        resource_native_id = keys[1] if len(keys) > 1 else None

                        # Clean up "NoResourceId" placeholder returned by AWS
                        if resource_native_id in ("NoResourceId", "Not Specified", ""):
                            resource_native_id = None

                        metrics = group.get("Metrics", {})
                        unblended_raw = metrics.get("UnblendedCost", {}).get("Amount", "0.0")
                        amortized_raw = metrics.get("AmortizedCost", {}).get("Amount", "0.0")
                        currency = metrics.get("UnblendedCost", {}).get("Unit", "USD")

                        unblended_cost = Decimal(str(unblended_raw)).quantize(
                            Decimal("0.0001"), rounding=ROUND_HALF_UP
                        )
                        amortized_cost = Decimal(str(amortized_raw)).quantize(
                            Decimal("0.0001"), rounding=ROUND_HALF_UP
                        )

                        if unblended_cost == Decimal("0.0000") and amortized_cost == Decimal("0.0000"):
                            continue

                        attribution_level = (
                            CostAttributionLevel.RESOURCE
                            if resource_native_id
                            else CostAttributionLevel.SERVICE
                        )

                        source_key = self._generate_source_record_key(
                            account_id=account_id,
                            usage_date=period_date,
                            service_name=service_name,
                            resource_id=resource_native_id,
                            region=None,
                            usage_type=None,
                            operation=None,
                            usage_unit=None,
                            attribution_level=attribution_level,
                        )

                        records.append(
                            DiscoveredCostRecord(
                                usage_date=period_date,
                                service_name=service_name,
                                unblended_cost=unblended_cost,
                                amortized_cost=amortized_cost,
                                usage_quantity=None,
                                usage_unit=None,
                                usage_type=None,
                                operation=None,
                                currency=currency,
                                resource_native_id=resource_native_id,
                                attribution_level=attribution_level,
                                source_record_key=source_key,
                            )
                        )

                next_token = response.get("NextPageToken")
                if not next_token:
                    break

            return records, True, None

        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "Unknown")
            msg = e.response.get("Error", {}).get("Message", str(e))
            logger.warning(
                "Resource-level cost attribution unavailable for account %s: %s - %s",
                account_id,
                code,
                msg,
            )
            return [], False, f"{code}: {msg}"
        except Exception as e:
            logger.warning("Resource-level cost retrieval failed: %s", str(e))
            return [], False, str(e)
