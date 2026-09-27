"""
NEXORA ATLAS - Demo Event Metadata
Defines domain-neutral operational events embedded in the synthetic dataset.
The dashboard service consumes these via a clean interface rather than hardcoding fixture details.
"""

from dataclasses import dataclass, asdict
from datetime import date, timedelta
from typing import List, Optional, Dict, Any
from app.demo.config import REFERENCE_START_DATE


@dataclass(frozen=True)
class DemoEvent:
    id: str
    occurred_at: date
    title: str
    description: str
    category: str
    impact_service: str
    related_resource_native_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["occurred_at"] = self.occurred_at.isoformat()
        return d


def get_demo_events() -> List[DemoEvent]:
    """
    Returns the 4 operational events embedded in the Phase 3 synthetic dataset.
    Anchored to reference dates matching the generator.
    """
    return [
        DemoEvent(
            id="evt-eks-scale",
            occurred_at=REFERENCE_START_DATE + timedelta(days=30),  # Day -60
            title="Analytics EKS Cluster Scale-Out",
            description="Added 2 c5.2xlarge worker nodes to handle scheduled batch ETL pipeline workload increase.",
            category="SCALING",
            impact_service="AmazonEKS",
            related_resource_native_id="i-0eks-w-05",
        ),
        DemoEvent(
            id="evt-gpu-burst",
            occurred_at=REFERENCE_START_DATE + timedelta(days=45),  # Day -45
            title="AI/GPU Fine-Tuning Surge",
            description="Temporary 10-day burst running multi-modal LLM evaluation on g4dn.2xlarge GPU instances.",
            category="BURST_WORKLOAD",
            impact_service="AmazonEC2",
            related_resource_native_id="i-0gpu-g4dn-2x-01",
        ),
        DemoEvent(
            id="evt-ebs-orphan",
            occurred_at=REFERENCE_START_DATE + timedelta(days=72),  # Day -18
            title="Orphan EBS Volume Accumulation",
            description="Dev CI/CD test run failed to purge 4 attached EBS gp3 volumes after tear-down.",
            category="STORAGE_LEAK",
            impact_service="AmazonEC2",
            related_resource_native_id="vol-0e5f6a7b8c9d0006",
        ),
        DemoEvent(
            id="evt-api-spike",
            occurred_at=REFERENCE_START_DATE + timedelta(days=87),  # Day -3
            title="Production API Auto-Scaling Spike",
            description="Unindexed database query triggered connection pool exhaustion, driving auto-scaler to max capacity.",
            category="INCIDENT",
            impact_service="AmazonEC2",
            related_resource_native_id="i-0a1b2c3d4e5f0001",
        ),
    ]
