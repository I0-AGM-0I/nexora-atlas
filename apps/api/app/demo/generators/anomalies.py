"""
NEXORA ATLAS - Anomaly Generator
Generates deterministic anomalies derived directly from simulated historical cost events.
Preserves strict separation between Observed data and Inferences.
"""

from decimal import Decimal
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any


def generate_anomalies(
    account_map: Dict[str, str],   # raw account_id -> DB uuid
    resource_map: Dict[str, str],  # native_id -> DB uuid
) -> List[Dict[str, Any]]:
    prod_acc_id = account_map["111222333444"]
    staging_acc_id = account_map["222333444555"]
    now_utc = datetime(2026, 9, 15, 8, 30, 0, tzinfo=timezone.utc)

    anomalies: List[Dict[str, Any]] = [
        # Anomaly 1: Production Core API EC2 Auto-Scaling Spike
        {
            "account_id": prod_acc_id,
            "resource_id": resource_map.get("i-0a1b2c3d4e5f0001"),
            "service_name": "AmazonEC2",
            "observed_cost": Decimal("470000.0000"),
            "baseline_cost": Decimal("340000.0000"),
            "percentage_change": Decimal("38.24"),
            "detected_at": now_utc - timedelta(days=2),
            "detection_rule": "ROLLING_ZSCORE_EXCEEDED",
            "observed_metrics_json": {
                "observed_compute_hours": 2880,
                "baseline_compute_hours": 2080,
                "scaling_trigger": "alb_request_count_per_target",
                "sample_window_days": 14,
            },
            "severity": "HIGH",
            "status": "OPEN",
            "inferred_cause": "Increased compute hours correlated with unindexed database query retry storms in production API tier.",
            "confidence_pct": Decimal("91.50"),
            "inference_details_json": {
                "correlated_service": "AmazonRDS",
                "affected_instance_types": ["m5.2xlarge"],
                "algorithm": "IQR_DEVIATION_DETECTOR",
            },
        },
        # Anomaly 2: AI / GPU Inference Cluster Surge
        {
            "account_id": prod_acc_id,
            "resource_id": resource_map.get("i-0gpu-g4dn-2x-01"),
            "service_name": "AmazonEC2",
            "observed_cost": Decimal("190000.0000"),
            "baseline_cost": Decimal("125000.0000"),
            "percentage_change": Decimal("52.00"),
            "detected_at": now_utc - timedelta(days=5),
            "detection_rule": "SUDDEN_SPIKE_DETECTED",
            "observed_metrics_json": {
                "active_gpu_hours": 2160,
                "baseline_gpu_hours": 1420,
                "gpu_utilization_p95": 86.4,
                "sample_window_days": 10,
            },
            "severity": "HIGH",
            "status": "OPEN",
            "inferred_cause": "New deep-learning inference model deployed to production with higher compute demand per token.",
            "confidence_pct": Decimal("88.00"),
            "inference_details_json": {
                "workload": "model-inference",
                "instance_family": "g4dn",
                "algorithm": "MOVING_AVERAGE_RATIO",
            },
        },
        # Anomaly 3: S3 Data Lake Unmanaged Growth
        {
            "account_id": prod_acc_id,
            "resource_id": resource_map.get("nexora-raw-data-lake"),
            "service_name": "AmazonS3",
            "observed_cost": Decimal("145000.0000"),
            "baseline_cost": Decimal("117000.0000"),
            "percentage_change": Decimal("23.93"),
            "detected_at": now_utc - timedelta(days=8),
            "detection_rule": "HISTORICAL_GROWTH_VIOLATION",
            "observed_metrics_json": {
                "current_size_tb": 48.5,
                "starting_size_tb": 39.1,
                "daily_growth_gb": 315,
                "lifecycle_policies_found": 0,
            },
            "severity": "MEDIUM",
            "status": "OPEN",
            "inferred_cause": "Continuous telemetry accumulation without retention or transition rules to cold storage.",
            "confidence_pct": Decimal("84.00"),
            "inference_details_json": {
                "bucket": "nexora-raw-data-lake",
                "recommendation_link": "OPP-STORAGE-01",
            },
        },
        # Anomaly 4: Staging Data Transfer Egress Burst
        {
            "account_id": staging_acc_id,
            "resource_id": resource_map.get("i-staging-t3l-01"),
            "service_name": "AmazonEC2",
            "observed_cost": Decimal("38000.0000"),
            "baseline_cost": Decimal("23000.0000"),
            "percentage_change": Decimal("65.22"),
            "detected_at": now_utc - timedelta(days=12),
            "detection_rule": "THRESHOLD_MULTIPLIER_2X",
            "observed_metrics_json": {
                "egress_gb": 8400,
                "baseline_egress_gb": 4800,
                "destination": "internet",
            },
            "severity": "LOW",
            "status": "ACKNOWLEDGED",
            "inferred_cause": "Load-testing automation script transferred full database dump across public internet instead of VPC peering.",
            "confidence_pct": Decimal("79.50"),
            "inference_details_json": {
                "test_suite": "integration-e2e-run-412",
            },
        },
    ]

    return anomalies
