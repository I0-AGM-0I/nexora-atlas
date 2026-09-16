"""
NEXORA ATLAS - Scenario Generator
Creates deterministic infrastructure simulation models (Options A, B, C).
Guarantees mathematical reconciliation between baseline, projected, savings, and delta changes.
"""

from decimal import Decimal
from typing import List, Dict, Any


def generate_scenarios(
    org_id: str,
    resource_map: Dict[str, str],
) -> List[Dict[str, Any]]:
    baseline = Decimal("2140000.0000")

    scenarios = [
        # Option A: Conservative Right-Sizing & Schedule Automation
        {
            "org_id": org_id,
            "name": "Option A: Conservative (Zero-Downtime Cleanups & Schedules)",
            "description": "Automates non-production off-hours schedules, deletes orphaned storage, and upgrades legacy EBS to gp3 with zero risk to production traffic.",
            "baseline_monthly_cost": baseline,
            "projected_monthly_cost": Decimal("1890000.0000"),
            "monthly_savings": Decimal("250000.0000"),
            "percentage_savings": Decimal("11.68"),
            "performance_risk": "NONE",
            "reliability_risk": "NONE",
            "complexity_level": "LOW",
            "assumptions_json": {
                "dev_schedule": "Monday-Friday 09:00-18:00 IST",
                "production_impact": "None",
                "rollback_time_hours": 0,
            },
            "changes": [
                {
                    "resource_id": resource_map.get("i-dev-sandbox-t3x-01"),
                    "change_type": "SCHEDULE_OFF_HOURS",
                    "current_spec": "6x Development EC2 instances running 24/7 (720 hrs/mo)",
                    "proposed_spec": "Automated schedule: 45 active hours/week (180 hrs/mo)",
                    "delta_cost": Decimal("-92000.0000"),
                },
                {
                    "resource_id": resource_map.get("vol-unattached-dev-01"),
                    "change_type": "TERMINATE_UNATTACHED",
                    "current_spec": "3 unattached gp2 volumes (1200 GB)",
                    "proposed_spec": "Snapshot and terminate detached storage",
                    "delta_cost": Decimal("-18000.0000"),
                },
                {
                    "resource_id": resource_map.get("vol-legacy-gp2-analytics-01"),
                    "change_type": "TIER_STORAGE_GP3",
                    "current_spec": "2x 1000 GB gp2 volumes on Analytics",
                    "proposed_spec": "2x 1000 GB gp3 volumes (20% lower baseline cost)",
                    "delta_cost": Decimal("-26000.0000"),
                },
                {
                    "resource_id": resource_map.get("eipalloc-orphan-01"),
                    "change_type": "RELEASE_IP",
                    "current_spec": "2 unallocated Elastic IP addresses",
                    "proposed_spec": "Release IPs back to pool",
                    "delta_cost": Decimal("-4000.0000"),
                },
                {
                    "resource_id": resource_map.get("nexora-raw-data-lake"),
                    "change_type": "LIFECYCLE_TIERING",
                    "current_spec": "Standard S3 storage for all data lake objects",
                    "proposed_spec": "Transition data > 60 days to Glacier Instant Retrieval",
                    "delta_cost": Decimal("-110000.0000"),
                },
            ],
        },
        # Option B: Balanced Optimization
        {
            "org_id": org_id,
            "name": "Option B: Balanced (Schedules, S3 Tiering & Dev RDS Pause)",
            "description": "Combines Option A cleanups with automated Dev RDS instance shutdown and full 30-day S3 lifecycle management.",
            "baseline_monthly_cost": baseline,
            "projected_monthly_cost": Decimal("1770000.0000"),
            "monthly_savings": Decimal("370000.0000"),
            "percentage_savings": Decimal("17.29"),
            "performance_risk": "LOW",
            "reliability_risk": "LOW",
            "complexity_level": "MEDIUM",
            "assumptions_json": {
                "dev_rds_auto_pause": True,
                "s3_glacier_ir_latency": "Milliseconds",
            },
            "changes": [
                {
                    "resource_id": resource_map.get("i-dev-sandbox-t3x-01"),
                    "change_type": "SCHEDULE_OFF_HOURS",
                    "current_spec": "6x Development EC2 instances running 24/7",
                    "proposed_spec": "Automated schedule: 45 active hours/week",
                    "delta_cost": Decimal("-92000.0000"),
                },
                {
                    "resource_id": resource_map.get("dev-microservice-db-01"),
                    "change_type": "PAUSE_IDLE_RDS",
                    "current_spec": "2x db.t3.small running 24/7",
                    "proposed_spec": "Stop dev databases outside testing sprints",
                    "delta_cost": Decimal("-38000.0000"),
                },
                {
                    "resource_id": resource_map.get("vol-unattached-dev-01"),
                    "change_type": "TERMINATE_UNATTACHED",
                    "current_spec": "3 unattached gp2 volumes (1200 GB)",
                    "proposed_spec": "Snapshot and terminate detached storage",
                    "delta_cost": Decimal("-18000.0000"),
                },
                {
                    "resource_id": resource_map.get("vol-legacy-gp2-analytics-01"),
                    "change_type": "TIER_STORAGE_GP3",
                    "current_spec": "2x 1000 GB gp2 volumes",
                    "proposed_spec": "2x 1000 GB gp3 volumes",
                    "delta_cost": Decimal("-26000.0000"),
                },
                {
                    "resource_id": resource_map.get("eipalloc-orphan-01"),
                    "change_type": "RELEASE_IP",
                    "current_spec": "2 unallocated Elastic IPs",
                    "proposed_spec": "Release IPs to pool",
                    "delta_cost": Decimal("-4000.0000"),
                },
                {
                    "resource_id": resource_map.get("nexora-raw-data-lake"),
                    "change_type": "LIFECYCLE_TIERING",
                    "current_spec": "Standard S3 storage indefinitely",
                    "proposed_spec": "Transition data > 30 days to Glacier IR; expire non-current versions",
                    "delta_cost": Decimal("-140000.0000"),
                },
                {
                    "resource_id": resource_map.get("i-0eks-node-m5-4x-01"),
                    "change_type": "PARTIAL_RIGHTSIZE",
                    "current_spec": "6x m5.4xlarge nodes",
                    "proposed_spec": "Scale node group down to 4 nodes with Karpenter autoscaling",
                    "delta_cost": Decimal("-52000.0000"),
                },
            ],
        },
        # Option C: Aggressive Optimization
        {
            "org_id": org_id,
            "name": "Option C: Aggressive (Full EKS Right-Sizing & Spot Adoption)",
            "description": "Maximizes cost reduction across compute, storage, and database. Right-sizes analytics cluster nodes to m5.large and enforces full storage tiering.",
            "baseline_monthly_cost": baseline,
            "projected_monthly_cost": Decimal("1680000.0000"),
            "monthly_savings": Decimal("460000.0000"),
            "percentage_savings": Decimal("21.50"),
            "performance_risk": "LOW",
            "reliability_risk": "MEDIUM",
            "complexity_level": "MEDIUM",
            "assumptions_json": {
                "eks_rightsizing": "m5.4xlarge -> m5.large",
                "maximum_achievable_monthly_reduction": "₹4.6 Lakhs",
            },
            "changes": [
                {
                    "resource_id": resource_map.get("i-0eks-node-m5-4x-01"),
                    "change_type": "RIGHTSIZE_COMPUTE",
                    "current_spec": "6x m5.4xlarge nodes (16 vCPU, 64 GB)",
                    "proposed_spec": "6x m5.large nodes (2 vCPU, 8 GB)",
                    "delta_cost": Decimal("-142000.0000"),
                },
                {
                    "resource_id": resource_map.get("i-dev-sandbox-t3x-01"),
                    "change_type": "SCHEDULE_OFF_HOURS",
                    "current_spec": "6x Development EC2 instances running 24/7",
                    "proposed_spec": "Automated schedule: 45 active hours/week",
                    "delta_cost": Decimal("-92000.0000"),
                },
                {
                    "resource_id": resource_map.get("nexora-raw-data-lake"),
                    "change_type": "LIFECYCLE_TIERING",
                    "current_spec": "Standard S3 storage indefinitely",
                    "proposed_spec": "Transition data > 30 days to Glacier IR; expire non-current versions",
                    "delta_cost": Decimal("-140000.0000"),
                },
                {
                    "resource_id": resource_map.get("dev-microservice-db-01"),
                    "change_type": "PAUSE_IDLE_RDS",
                    "current_spec": "2x db.t3.small running 24/7",
                    "proposed_spec": "Stop dev databases outside testing sprints",
                    "delta_cost": Decimal("-38000.0000"),
                },
                {
                    "resource_id": resource_map.get("vol-legacy-gp2-analytics-01"),
                    "change_type": "TIER_STORAGE_GP3",
                    "current_spec": "2x 1000 GB gp2 volumes",
                    "proposed_spec": "2x 1000 GB gp3 volumes",
                    "delta_cost": Decimal("-26000.0000"),
                },
                {
                    "resource_id": resource_map.get("vol-unattached-dev-01"),
                    "change_type": "TERMINATE_UNATTACHED",
                    "current_spec": "3 unattached gp2 volumes (1200 GB)",
                    "proposed_spec": "Snapshot and terminate detached storage",
                    "delta_cost": Decimal("-18000.0000"),
                },
                {
                    "resource_id": resource_map.get("eipalloc-orphan-01"),
                    "change_type": "RELEASE_IP",
                    "current_spec": "2 unallocated Elastic IPs",
                    "proposed_spec": "Release IPs to pool",
                    "delta_cost": Decimal("-4000.0000"),
                },
            ],
        },
    ]

    return scenarios
