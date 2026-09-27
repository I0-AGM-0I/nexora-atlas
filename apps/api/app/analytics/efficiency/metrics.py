"""
NEXORA ATLAS - Efficiency & Headroom Metrics
Calculates observed capacity headroom while strictly distinguishing utilization from removable capacity.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, Any, Tuple

from app.analytics.types import SufficiencyStatus
from app.analytics.models import HeadroomItem


def calculate_observed_utilization_headroom(
    p95_utilization: Optional[Decimal],
) -> Optional[Decimal]:
    """
    Calculates: observed_utilization_headroom = 100% - p95_utilization.

    IMPORTANT ARCHITECTURAL RULE:
    Observed utilization headroom represents the mathematical difference between 100%
    and the observed 95th percentile utilization. It is NOT interpreted as directly
    removable infrastructure capacity without Phase 5 evidence-backed recommendations.
    """
    if p95_utilization is None:
        return None
    headroom = (Decimal("100.00") - p95_utilization).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return max(Decimal("0.00"), headroom)


def extract_resource_headroom(
    resource_id: str,
    resource_name: str,
    service_name: str,
    specs: Dict[str, Any],
) -> HeadroomItem:
    """
    Extracts p95 utilization and headroom from resource specifications and telemetry.
    Returns SufficiencyStatus.AVAILABLE if telemetry exists, else INSUFFICIENT_DATA or NOT_APPLICABLE.
    """
    if service_name not in ("AmazonEC2", "AmazonRDS"):
        return HeadroomItem(
            resource_id=resource_id,
            resource_name=resource_name,
            service_name=service_name,
            sufficiency_status=SufficiencyStatus.NOT_APPLICABLE,
        )

    # Check for telemetry in specs
    cpu_val = specs.get("cpu_utilization_p95") or specs.get("p95_cpu_utilization_pct") or specs.get("avg_cpu_pct")
    mem_val = specs.get("memory_utilization_p95") or specs.get("p95_memory_utilization_pct") or specs.get("avg_memory_pct")

    p95_cpu: Optional[Decimal] = None
    p95_mem: Optional[Decimal] = None

    if cpu_val is not None:
        try:
            p95_cpu = Decimal(str(cpu_val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except Exception:
            pass

    if mem_val is not None:
        try:
            p95_mem = Decimal(str(mem_val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except Exception:
            pass

    if p95_cpu is None and p95_mem is None:
        if "instance_type" not in specs:
            return HeadroomItem(
                resource_id=resource_id,
                resource_name=resource_name,
                service_name=service_name,
                sufficiency_status=SufficiencyStatus.NOT_APPLICABLE,
            )
        return HeadroomItem(
            resource_id=resource_id,
            resource_name=resource_name,
            service_name=service_name,
            instance_type=specs.get("instance_type"),
            sufficiency_status=SufficiencyStatus.INSUFFICIENT_DATA,
        )

    headroom_cpu = calculate_observed_utilization_headroom(p95_cpu)
    headroom_mem = calculate_observed_utilization_headroom(p95_mem)

    return HeadroomItem(
        resource_id=resource_id,
        resource_name=resource_name,
        service_name=service_name,
        instance_type=specs.get("instance_type"),
        p95_utilization_cpu=p95_cpu,
        p95_utilization_memory=p95_mem,
        observed_utilization_headroom_cpu=headroom_cpu,
        observed_utilization_headroom_memory=headroom_mem,
        sufficiency_status=SufficiencyStatus.AVAILABLE,
    )
