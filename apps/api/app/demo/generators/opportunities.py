"""
NEXORA ATLAS - Optimization Opportunities & Recommendations Generator
Creates explainable waste detections and actionable recommendations.
Guarantees mathematical reconciliation: Monthly * 12 = Annual, Sum = ₹4.6 Lakhs/mo.
"""

from decimal import Decimal
from typing import List, Dict, Tuple, Any


def generate_opportunities_and_recommendations(
    account_map: Dict[str, str],   # raw account_id -> DB uuid
    resource_map: Dict[str, str],  # native_id -> DB uuid
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    prod_acc_id = account_map["111222333444"]
    dev_acc_id = account_map["333444555666"]

    opportunities_data: List[Dict[str, Any]] = []
    recommendations_data: List[Dict[str, Any]] = []

    # 1. Opportunity 1: Oversized Analytics EKS Worker Nodes
    opp1 = {
        "_ref": "opp-eks-oversized",
        "account_id": prod_acc_id,
        "resource_id": resource_map.get("analytics-eks-cluster"),
        "category": "COMPUTE",
        "waste_type": "OVERSIZED_INSTANCE",
        "severity": "HIGH",
        "status": "OPEN",
        "estimated_waste_monthly": Decimal("142000.0000"),
        "evidence_json": {
            "cluster": "analytics-eks-cluster",
            "node_count": 6,
            "instance_type": "m5.4xlarge",
            "p95_cpu_utilization_pct": 11.2,
            "p95_memory_utilization_pct": 18.4,
            "observed_window_days": 30,
            "observed_pattern": "Workload is memory-light; provisioned vCPUs consistently idle.",
        },
    }
    opportunities_data.append(opp1)

    # Opportunity 1 produces TWO candidate recommendations (Option 1 = primary, Option 2 = Graviton alternative)
    recommendations_data.append({
        "opportunity_ref": "opp-eks-oversized",
        "resource_id": resource_map.get("i-0eks-node-m5-4x-01"),
        "category": "COMPUTE",
        "title": "Downsize Analytics EKS Node Group to m5.large",
        "current_configuration": "6x m5.4xlarge (16 vCPU, 64 GB RAM)",
        "recommended_configuration": "6x m5.large (2 vCPU, 8 GB RAM)",
        "estimated_monthly_savings": Decimal("142000.0000"),
        "estimated_annual_savings": Decimal("1704000.0000"),
        "confidence_pct": Decimal("94.00"),
        "risk_level": "LOW",
        "reasoning": "Cluster metrics show sustained 30-day peak demand under 12 vCPU aggregate across all nodes.",
        "evidence_json": {
            "p95_cpu_pct": 11.2,
            "p95_ram_pct": 18.4,
            "downsize_ratio": "4:1",
        },
        "status": "OPEN",
    })
    recommendations_data.append({
        "opportunity_ref": "opp-eks-oversized",
        "resource_id": resource_map.get("i-0eks-node-m5-4x-01"),
        "category": "COMPUTE",
        "title": "Migrate Analytics EKS Node Group to Graviton c7g.xlarge",
        "current_configuration": "6x m5.4xlarge (16 vCPU, 64 GB RAM, x86)",
        "recommended_configuration": "6x c7g.xlarge (4 vCPU, 8 GB RAM, ARM64)",
        "estimated_monthly_savings": Decimal("165000.0000"),
        "estimated_annual_savings": Decimal("1980000.0000"),
        "confidence_pct": Decimal("82.00"),
        "risk_level": "MEDIUM",
        "reasoning": "ARM64 Graviton instances offer superior price/performance; requires multi-arch container verification.",
        "evidence_json": {
            "architecture_change": "x86_64 -> arm64",
            "container_compatibility": "pending_verification",
        },
        "status": "OPEN",
    })

    # 2. Opportunity 2: Dev Environment Running 24/7 Outside Business Hours
    opp2 = {
        "_ref": "opp-dev-offhours",
        "account_id": dev_acc_id,
        "resource_id": resource_map.get("i-dev-sandbox-t3x-01"),
        "category": "COMPUTE",
        "waste_type": "OFF_HOURS_IDLE",
        "severity": "HIGH",
        "status": "OPEN",
        "estimated_waste_monthly": Decimal("92000.0000"),
        "evidence_json": {
            "running_hours_per_week": 168,
            "target_hours_per_week": 45,
            "waste_hours_per_week": 123,
            "observed_off_hours_cpu_pct": 0.8,
        },
    }
    opportunities_data.append(opp2)

    recommendations_data.append({
        "opportunity_ref": "opp-dev-offhours",
        "resource_id": resource_map.get("i-dev-sandbox-t3x-01"),
        "category": "COMPUTE",
        "title": "Implement Off-Hours Automated Shutdown for Dev EC2",
        "current_configuration": "6 development sandbox instances running 24/7 (720 hrs/mo)",
        "recommended_configuration": "Automated schedule: Monday–Friday 09:00–18:00 IST (180 hrs/mo)",
        "estimated_monthly_savings": Decimal("92000.0000"),
        "estimated_annual_savings": Decimal("1104000.0000"),
        "confidence_pct": Decimal("96.00"),
        "risk_level": "LOW",
        "reasoning": "Zero developer commit or network activity logged between 19:00 and 08:30 IST over 90 days.",
        "evidence_json": {"active_business_hours": "09:00-18:00 IST", "weekend_policy": "STOPPED"},
        "status": "OPEN",
    })

    # 3. Opportunity 3: Idle Dev RDS Database Clusters
    opp3 = {
        "_ref": "opp-dev-rds-idle",
        "account_id": dev_acc_id,
        "resource_id": resource_map.get("dev-microservice-db-01"),
        "category": "DATABASE",
        "waste_type": "IDLE_DATABASE",
        "severity": "MEDIUM",
        "status": "OPEN",
        "estimated_waste_monthly": Decimal("38000.0000"),
        "evidence_json": {
            "active_client_connections": 0,
            "idle_duration_pct": 88.5,
            "iops_utilization_pct": 1.2,
        },
    }
    opportunities_data.append(opp3)

    recommendations_data.append({
        "opportunity_ref": "opp-dev-rds-idle",
        "resource_id": resource_map.get("dev-microservice-db-01"),
        "category": "DATABASE",
        "title": "Snapshot and Pause Idle Development RDS Databases",
        "current_configuration": "2x db.t3.small instances running continuously",
        "recommended_configuration": "Stop instances during non-testing periods; snapshot retention",
        "estimated_monthly_savings": Decimal("38000.0000"),
        "estimated_annual_savings": Decimal("456000.0000"),
        "confidence_pct": Decimal("92.00"),
        "risk_level": "LOW",
        "reasoning": "Database connections dropped to zero for 22 consecutive days.",
        "evidence_json": {"connection_count": 0, "idle_days": 22},
        "status": "OPEN",
    })

    # 4. Opportunity 4: Unattached EBS Volumes
    opp4 = {
        "_ref": "opp-ebs-unattached",
        "account_id": dev_acc_id,
        "resource_id": resource_map.get("vol-unattached-dev-01"),
        "category": "STORAGE",
        "waste_type": "UNATTACHED_VOLUME",
        "severity": "MEDIUM",
        "status": "OPEN",
        "estimated_waste_monthly": Decimal("18000.0000"),
        "evidence_json": {
            "unattached_volume_count": 3,
            "total_unattached_gb": 1200,
            "unattached_duration_days": 18,
            "volume_status": "AVAILABLE",
        },
    }
    opportunities_data.append(opp4)

    recommendations_data.append({
        "opportunity_ref": "opp-ebs-unattached",
        "resource_id": resource_map.get("vol-unattached-dev-01"),
        "category": "STORAGE",
        "title": "Snapshot and Delete Unattached EBS Volumes",
        "current_configuration": "3 detached gp2 volumes (1200 GB total)",
        "recommended_configuration": "Create final snapshot and delete unattached volumes",
        "estimated_monthly_savings": Decimal("18000.0000"),
        "estimated_annual_savings": Decimal("216000.0000"),
        "confidence_pct": Decimal("99.00"),
        "risk_level": "LOW",
        "reasoning": "Volumes have been detached for over two weeks following test container teardown.",
        "evidence_json": {"volume_ids": ["vol-unattached-dev-01", "vol-unattached-dev-02", "vol-unattached-dev-03"]},
        "status": "OPEN",
    })

    # 5. Opportunity 5: Legacy gp2 to gp3 Storage Migration
    opp5 = {
        "_ref": "opp-ebs-gp3-migration",
        "account_id": prod_acc_id,
        "resource_id": resource_map.get("vol-legacy-gp2-analytics-01"),
        "category": "STORAGE",
        "waste_type": "LEGACY_STORAGE_TIER",
        "severity": "MEDIUM",
        "status": "OPEN",
        "estimated_waste_monthly": Decimal("26000.0000"),
        "evidence_json": {
            "volume_type": "gp2",
            "volume_count": 2,
            "total_gb": 2000,
            "gp3_price_reduction_pct": 20.0,
        },
    }
    opportunities_data.append(opp5)

    recommendations_data.append({
        "opportunity_ref": "opp-ebs-gp3-migration",
        "resource_id": resource_map.get("vol-legacy-gp2-analytics-01"),
        "category": "STORAGE",
        "title": "Migrate Analytics EBS Volumes from gp2 to gp3",
        "current_configuration": "2x 1000 GB gp2 volumes (₹360/day)",
        "recommended_configuration": "2x 1000 GB gp3 volumes (3,000 IOPS baseline, 20% lower cost)",
        "estimated_monthly_savings": Decimal("26000.0000"),
        "estimated_annual_savings": Decimal("312000.0000"),
        "confidence_pct": Decimal("98.00"),
        "risk_level": "NONE",
        "reasoning": "AWS gp3 delivers equal or better performance at a baseline 20% price reduction with zero downtime migration.",
        "evidence_json": {"gp2_cost_per_gb": 0.10, "gp3_cost_per_gb": 0.08},
        "status": "OPEN",
    })

    # 6. Opportunity 6: Unassociated Elastic IPs
    opp6 = {
        "_ref": "opp-eip-unassociated",
        "account_id": dev_acc_id,
        "resource_id": resource_map.get("eipalloc-orphan-01"),
        "category": "NETWORKING",
        "waste_type": "UNASSOCIATED_EIP",
        "severity": "LOW",
        "status": "OPEN",
        "estimated_waste_monthly": Decimal("4000.0000"),
        "evidence_json": {
            "idle_eip_count": 2,
            "idle_duration_days": 28,
        },
    }
    opportunities_data.append(opp6)

    recommendations_data.append({
        "opportunity_ref": "opp-eip-unassociated",
        "resource_id": resource_map.get("eipalloc-orphan-01"),
        "category": "NETWORKING",
        "title": "Release Unassociated Static Elastic IPs",
        "current_configuration": "2 unallocated Elastic IPs in ap-south-1",
        "recommended_configuration": "Release IP addresses to pool",
        "estimated_monthly_savings": Decimal("4000.0000"),
        "estimated_annual_savings": Decimal("48000.0000"),
        "confidence_pct": Decimal("100.00"),
        "risk_level": "NONE",
        "reasoning": "AWS charges hourly for IPv4 addresses reserved without an active running instance attachment.",
        "evidence_json": {"eips": ["eipalloc-orphan-01", "eipalloc-orphan-02"]},
        "status": "OPEN",
    })

    # 7. Opportunity 7: S3 Non-Current Version Accumulation
    opp7 = {
        "_ref": "opp-s3-lifecycle",
        "account_id": prod_acc_id,
        "resource_id": resource_map.get("nexora-raw-data-lake"),
        "category": "STORAGE",
        "waste_type": "UNMANAGED_OBJECT_VERSIONS",
        "severity": "HIGH",
        "status": "OPEN",
        "estimated_waste_monthly": Decimal("140000.0000"),
        "evidence_json": {
            "bucket": "nexora-raw-data-lake",
            "non_current_versions_gb": 18400,
            "incomplete_multipart_uploads_gb": 3200,
            "untiered_objects_older_90d_gb": 22100,
        },
    }
    opportunities_data.append(opp7)

    recommendations_data.append({
        "opportunity_ref": "opp-s3-lifecycle",
        "resource_id": resource_map.get("nexora-raw-data-lake"),
        "category": "STORAGE",
        "title": "Configure S3 Lifecycle Expiration & Glacier Instant Retrieval Tiering",
        "current_configuration": "All raw data retained indefinitely in S3 Standard",
        "recommended_configuration": "Transition to Glacier Instant Retrieval after 30 days; expire non-current versions after 14 days",
        "estimated_monthly_savings": Decimal("140000.0000"),
        "estimated_annual_savings": Decimal("1680000.0000"),
        "confidence_pct": Decimal("89.00"),
        "risk_level": "LOW",
        "reasoning": "82% of data lake reads query objects created in the last 14 days; older data rarely accessed but stored at full standard rates.",
        "evidence_json": {"lifecycle_action": "TRANSITION_GLACIER_IR", "abort_incomplete_uploads_days": 7},
        "status": "OPEN",
    })

    return opportunities_data, recommendations_data
