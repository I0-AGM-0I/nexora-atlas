"""
NEXORA ATLAS - Resource Topologies and Workload Fixtures
Defines the 72 synthetic cloud resources and their metadata tags across Production, Staging, and Dev.
Specs describe configuration; operational telemetry is explicitly separated.
"""

from typing import List, Dict, Any


def get_resource_fixtures() -> List[Dict[str, Any]]:
    """Returns the comprehensive list of 72 resources with associated tags and baseline daily cost weights."""
    resources: List[Dict[str, Any]] = []

    # -------------------------------------------------------------
    # 1. PRODUCTION ACCOUNT (111222333444)
    # -------------------------------------------------------------
    prod_acc = "111222333444"

    # A. Production Web & API Tier (ap-south-1)
    # ALBs
    resources.append({
        "account_id": prod_acc,
        "region_code": "ap-south-1",
        "service_name": "AmazonEC2",
        "resource_type": "LoadBalancer",
        "native_id": "app/alb-prod-external/50dc6c495c0c9188",
        "resource_arn": "arn:aws:elasticloadbalancing:ap-south-1:111222333444:loadbalancer/app/alb-prod-external/50dc6c495c0c9188",
        "name": "alb-prod-external",
        "status": "ACTIVE",
        "specs_json": {"scheme": "internet-facing", "ip_address_type": "ipv4"},
        "base_daily_cost": 95.0,  # ~₹2,850/mo
        "tags": {"Environment": "production", "Team": "core-api", "Application": "api-gateway"},
    })
    resources.append({
        "account_id": prod_acc,
        "region_code": "ap-south-1",
        "service_name": "AmazonEC2",
        "resource_type": "LoadBalancer",
        "native_id": "app/alb-prod-internal/72ea8d412b1d7234",
        "resource_arn": "arn:aws:elasticloadbalancing:ap-south-1:111222333444:loadbalancer/app/alb-prod-internal/72ea8d412b1d7234",
        "name": "alb-prod-internal",
        "status": "ACTIVE",
        "specs_json": {"scheme": "internal", "ip_address_type": "ipv4"},
        "base_daily_cost": 75.0,
        "tags": {"Environment": "production", "Team": "core-api", "Application": "internal-mesh"},
    })

    # EC2 Core API Workers (4x m5.2xlarge)
    for i in range(1, 5):
        resources.append({
            "account_id": prod_acc,
            "region_code": "ap-south-1",
            "service_name": "AmazonEC2",
            "resource_type": "Instance",
            "native_id": f"i-0a1b2c3d4e5f00{i:02d}",
            "resource_arn": f"arn:aws:ec2:ap-south-1:111222333444:instance/i-0a1b2c3d4e5f00{i:02d}",
            "name": f"prod-api-worker-{i:02d}",
            "status": "ACTIVE",
            "specs_json": {"instance_type": "m5.2xlarge", "vcpus": 8, "memory_gb": 32, "arch": "x86_64"},
            "base_daily_cost": 820.0,  # ~₹24,600/mo each
            "tags": {"Environment": "production", "Team": "core-api", "Application": "api-server", "CostCenter": "CC-PROD-101"},
        })

    # EC2 Background Queue Processors (4x c5.2xlarge)
    for i in range(1, 5):
        resources.append({
            "account_id": prod_acc,
            "region_code": "ap-south-1",
            "service_name": "AmazonEC2",
            "resource_type": "Instance",
            "native_id": f"i-0c5b2c3d4e5f00{i:02d}",
            "resource_arn": f"arn:aws:ec2:ap-south-1:111222333444:instance/i-0c5b2c3d4e5f00{i:02d}",
            "name": f"prod-async-processor-{i:02d}",
            "status": "ACTIVE",
            "specs_json": {"instance_type": "c5.2xlarge", "vcpus": 8, "memory_gb": 16, "arch": "x86_64"},
            "base_daily_cost": 740.0,  # ~₹22,200/mo each
            "tags": {"Environment": "production", "Team": "core-api", "Application": "queue-worker", "CostCenter": "CC-PROD-101"},
        })

    # Aurora PostgreSQL Primary & Replica (db.r5.2xlarge)
    resources.append({
        "account_id": prod_acc,
        "region_code": "ap-south-1",
        "service_name": "AmazonRDS",
        "resource_type": "DBInstance",
        "native_id": "prod-aurora-cluster-primary",
        "resource_arn": "arn:aws:rds:ap-south-1:111222333444:db:prod-aurora-cluster-primary",
        "name": "prod-aurora-cluster-primary",
        "status": "ACTIVE",
        "specs_json": {"engine": "aurora-postgresql", "instance_class": "db.r5.2xlarge", "storage_gb": 1200},
        "base_daily_cost": 2900.0,  # ~₹87,000/mo
        "tags": {"Environment": "production", "Team": "platform", "Application": "database", "CostCenter": "CC-PROD-101"},
    })
    resources.append({
        "account_id": prod_acc,
        "region_code": "ap-south-1",
        "service_name": "AmazonRDS",
        "resource_type": "DBInstance",
        "native_id": "prod-aurora-cluster-replica",
        "resource_arn": "arn:aws:rds:ap-south-1:111222333444:db:prod-aurora-cluster-replica",
        "name": "prod-aurora-cluster-replica",
        "status": "ACTIVE",
        "specs_json": {"engine": "aurora-postgresql", "instance_class": "db.r5.2xlarge", "storage_gb": 1200},
        "base_daily_cost": 2800.0,  # ~₹84,000/mo
        "tags": {"Environment": "production", "Team": "platform", "Application": "database-replica", "CostCenter": "CC-PROD-101"},
    })

    # ElastiCache Redis Cluster (3x cache.r5.large)
    for i in range(1, 4):
        resources.append({
            "account_id": prod_acc,
            "region_code": "ap-south-1",
            "service_name": "AmazonElastiCache",
            "resource_type": "CacheCluster",
            "native_id": f"prod-redis-node-{i:02d}",
            "resource_arn": f"arn:aws:elasticache:ap-south-1:111222333444:cluster:prod-redis-node-{i:02d}",
            "name": f"prod-redis-node-{i:02d}",
            "status": "ACTIVE",
            "specs_json": {"node_type": "cache.r5.large", "engine": "redis", "num_nodes": 1},
            "base_daily_cost": 410.0,  # ~₹12,300/mo
            "tags": {"Environment": "production", "Team": "core-api", "Application": "cache"},
        })

    # NAT Gateways
    resources.append({
        "account_id": prod_acc,
        "region_code": "ap-south-1",
        "service_name": "AmazonVPC",
        "resource_type": "NatGateway",
        "native_id": "nat-0a123456789abcdef",
        "resource_arn": "arn:aws:ec2:ap-south-1:111222333444:natgateway/nat-0a123456789abcdef",
        "name": "nat-gw-prod-az1",
        "status": "ACTIVE",
        "specs_json": {"vpc_id": "vpc-prod-01", "subnet": "subnet-public-1"},
        "base_daily_cost": 310.0,
        "tags": {"Environment": "production", "Team": "platform"},
    })
    resources.append({
        "account_id": prod_acc,
        "region_code": "ap-south-1",
        "service_name": "AmazonVPC",
        "resource_type": "NatGateway",
        "native_id": "nat-0b987654321fedcba",
        "resource_arn": "arn:aws:ec2:ap-south-1:111222333444:natgateway/nat-0b987654321fedcba",
        "name": "nat-gw-prod-az2",
        "status": "ACTIVE",
        "specs_json": {"vpc_id": "vpc-prod-01", "subnet": "subnet-public-2"},
        "base_daily_cost": 310.0,
        "tags": {"Environment": "production", "Team": "platform"},
    })

    # Attached EBS gp3 volumes (4x 500GB)
    for i in range(1, 5):
        resources.append({
            "account_id": prod_acc,
            "region_code": "ap-south-1",
            "service_name": "AmazonEC2",
            "resource_type": "Volume",
            "native_id": f"vol-prod-ebs-{i:02d}",
            "resource_arn": f"arn:aws:ec2:ap-south-1:111222333444:volume/vol-prod-ebs-{i:02d}",
            "name": f"prod-root-volume-{i:02d}",
            "status": "IN_USE",
            "specs_json": {"volume_type": "gp3", "size_gb": 500, "iops": 3000, "throughput_mbps": 125},
            "base_daily_cost": 135.0,
            "tags": {"Environment": "production", "Team": "platform"},
        })

    # B. Analytics & Big Data Platform (us-west-2)
    # EKS Control Plane
    resources.append({
        "account_id": prod_acc,
        "region_code": "us-west-2",
        "service_name": "AmazonEKS",
        "resource_type": "Cluster",
        "native_id": "analytics-eks-cluster",
        "resource_arn": "arn:aws:eks:us-west-2:111222333444:cluster/analytics-eks-cluster",
        "name": "analytics-eks-cluster",
        "status": "ACTIVE",
        "specs_json": {"k8s_version": "1.29", "platform": "eks"},
        "base_daily_cost": 270.0,
        "tags": {"Environment": "production", "Team": "analytics", "Application": "data-platform"},
    })

    # 6x m5.4xlarge EKS Worker Nodes (OVERSIZED WASTE SCENARIO!)
    for i in range(1, 7):
        resources.append({
            "account_id": prod_acc,
            "region_code": "us-west-2",
            "service_name": "AmazonEC2",
            "resource_type": "Instance",
            "native_id": f"i-0eks-node-m5-4x-{i:02d}",
            "resource_arn": f"arn:aws:ec2:us-west-2:111222333444:instance/i-0eks-node-m5-4x-{i:02d}",
            "name": f"analytics-worker-node-{i:02d}",
            "status": "ACTIVE",
            "specs_json": {
                "instance_type": "m5.4xlarge",
                "vcpus": 16,
                "memory_gb": 64,
                "cluster": "analytics-eks-cluster",
                "p95_cpu_utilization_pct": 11.2,
                "p95_memory_utilization_pct": 18.4,
            },
            "base_daily_cost": 1640.0,  # ~₹49,200/mo each!
            "tags": {"Environment": "production", "Team": "analytics", "Application": "data-platform", "CostCenter": "CC-PROD-101"},
        })

    # Legacy EBS gp2 volumes on Analytics (2x 1000GB - gp2 to gp3 storage tiering opportunity!)
    for i in range(1, 3):
        resources.append({
            "account_id": prod_acc,
            "region_code": "us-west-2",
            "service_name": "AmazonEC2",
            "resource_type": "Volume",
            "native_id": f"vol-legacy-gp2-analytics-{i:02d}",
            "resource_arn": f"arn:aws:ec2:us-west-2:111222333444:volume/vol-legacy-gp2-analytics-{i:02d}",
            "name": f"analytics-legacy-storage-{i:02d}",
            "status": "IN_USE",
            "specs_json": {"volume_type": "gp2", "size_gb": 1000, "iops": 3000},
            "base_daily_cost": 360.0,
            "tags": {"Environment": "production", "Team": "analytics"},
        })

    # S3 Data Lake Buckets (Accumulating storage scenario)
    resources.append({
        "account_id": prod_acc,
        "region_code": "us-west-2",
        "service_name": "AmazonS3",
        "resource_type": "Bucket",
        "native_id": "nexora-raw-data-lake",
        "resource_arn": "arn:aws:s3:::nexora-raw-data-lake",
        "name": "nexora-raw-data-lake",
        "status": "ACTIVE",
        "specs_json": {
            "storage_class": "STANDARD",
            "approx_size_tb": 48.5,
            "versioning": "ENABLED",
            "non_current_versions_gb": 18400,
            "lifecycle_rules_found": 0,
        },
        "base_daily_cost": 1950.0,  # ~₹58,500/mo
        "tags": {"Environment": "production", "Team": "analytics", "Application": "data-lake"},
    })
    resources.append({
        "account_id": prod_acc,
        "region_code": "us-west-2",
        "service_name": "AmazonS3",
        "resource_type": "Bucket",
        "native_id": "nexora-analytics-warehouse",
        "resource_arn": "arn:aws:s3:::nexora-analytics-warehouse",
        "name": "nexora-analytics-warehouse",
        "status": "ACTIVE",
        "specs_json": {"storage_class": "STANDARD", "approx_size_tb": 32.0, "versioning": "ENABLED"},
        "base_daily_cost": 1400.0,
        "tags": {"Environment": "production", "Team": "analytics", "Application": "data-warehouse"},
    })
    resources.append({
        "account_id": prod_acc,
        "region_code": "us-west-2",
        "service_name": "AmazonS3",
        "resource_type": "Bucket",
        "native_id": "nexora-emr-scratch",
        "resource_arn": "arn:aws:s3:::nexora-emr-scratch",
        "name": "nexora-emr-scratch",
        "status": "ACTIVE",
        "specs_json": {"storage_class": "STANDARD", "approx_size_tb": 12.0, "versioning": "DISABLED"},
        "base_daily_cost": 520.0,
        "tags": {"Environment": "production", "Team": "analytics"},
    })

    # C. AI / Machine Learning Inference Tier (us-east-1)
    for i in range(1, 4):
        resources.append({
            "account_id": prod_acc,
            "region_code": "us-east-1",
            "service_name": "AmazonEC2",
            "resource_type": "Instance",
            "native_id": f"i-0gpu-g4dn-2x-{i:02d}",
            "resource_arn": f"arn:aws:ec2:us-east-1:111222333444:instance/i-0gpu-g4dn-2x-{i:02d}",
            "name": f"ml-inference-g4dn-{i:02d}",
            "status": "ACTIVE",
            "specs_json": {"instance_type": "g4dn.2xlarge", "gpus": 1, "gpu_type": "NVIDIA T4", "vcpus": 8, "memory_gb": 32},
            "base_daily_cost": 1850.0,  # ~₹55,500/mo each
            "tags": {"Environment": "production", "Team": "ml", "Application": "inference-engine", "CostCenter": "CC-AI-303"},
        })

    resources.append({
        "account_id": prod_acc,
        "region_code": "us-east-1",
        "service_name": "AmazonS3",
        "resource_type": "Bucket",
        "native_id": "nexora-ml-model-registry",
        "resource_arn": "arn:aws:s3:::nexora-ml-model-registry",
        "name": "nexora-ml-model-registry",
        "status": "ACTIVE",
        "specs_json": {"storage_class": "STANDARD", "approx_size_tb": 6.5},
        "base_daily_cost": 290.0,
        "tags": {"Environment": "production", "Team": "ml", "Application": "model-registry"},
    })

    # CloudFront Distribution & Global Data Transfer
    resources.append({
        "account_id": prod_acc,
        "region_code": "us-east-1",
        "service_name": "AmazonCloudFront",
        "resource_type": "Distribution",
        "native_id": "d123456abcdef8",
        "resource_arn": "arn:aws:cloudfront::111222333444:distribution/d123456abcdef8",
        "name": "nexora-cdn-global",
        "status": "ACTIVE",
        "specs_json": {"price_class": "PriceClass_All", "enabled": True},
        "base_daily_cost": 480.0,  # ~₹14,400/mo
        "tags": {"Environment": "production", "Team": "platform"},
    })

    # -------------------------------------------------------------
    # 2. STAGING ACCOUNT (222333444555)
    # -------------------------------------------------------------
    staging_acc = "222333444555"

    resources.append({
        "account_id": staging_acc,
        "region_code": "ap-south-1",
        "service_name": "AmazonEC2",
        "resource_type": "LoadBalancer",
        "native_id": "app/alb-staging/81fa6b215c0e1199",
        "resource_arn": "arn:aws:elasticloadbalancing:ap-south-1:222333444555:loadbalancer/app/alb-staging/81fa6b215c0e1199",
        "name": "alb-staging",
        "status": "ACTIVE",
        "specs_json": {"scheme": "internet-facing"},
        "base_daily_cost": 75.0,
        "tags": {"Environment": "staging", "Team": "core-api"},
    })

    for i in range(1, 5):
        resources.append({
            "account_id": staging_acc,
            "region_code": "ap-south-1",
            "service_name": "AmazonEC2",
            "resource_type": "Instance",
            "native_id": f"i-staging-t3l-{i:02d}",
            "resource_arn": f"arn:aws:ec2:ap-south-1:222333444555:instance/i-staging-t3l-{i:02d}",
            "name": f"staging-api-{i:02d}",
            "status": "ACTIVE",
            "specs_json": {"instance_type": "t3.large", "vcpus": 2, "memory_gb": 8},
            "base_daily_cost": 210.0,  # ~₹6,300/mo each
            "tags": {"Environment": "staging", "Team": "core-api", "CostCenter": "CC-ENG-202"},
        })

    resources.append({
        "account_id": staging_acc,
        "region_code": "ap-south-1",
        "service_name": "AmazonRDS",
        "resource_type": "DBInstance",
        "native_id": "staging-pg-db",
        "resource_arn": "arn:aws:rds:ap-south-1:222333444555:db:staging-pg-db",
        "name": "staging-pg-db",
        "status": "ACTIVE",
        "specs_json": {"engine": "postgres", "instance_class": "db.t3.medium", "storage_gb": 200},
        "base_daily_cost": 340.0,
        "tags": {"Environment": "staging", "Team": "core-api"},
    })

    resources.append({
        "account_id": staging_acc,
        "region_code": "ap-south-1",
        "service_name": "AmazonS3",
        "resource_type": "Bucket",
        "native_id": "nexora-staging-assets",
        "resource_arn": "arn:aws:s3:::nexora-staging-assets",
        "name": "nexora-staging-assets",
        "status": "ACTIVE",
        "specs_json": {"storage_class": "STANDARD", "approx_size_tb": 2.2},
        "base_daily_cost": 110.0,
        "tags": {"Environment": "staging", "Team": "core-api"},
    })

    # -------------------------------------------------------------
    # 3. DEVELOPMENT / SANDBOX ACCOUNT (333444555666)
    # -------------------------------------------------------------
    dev_acc = "333444555666"

    # Dev Instances (Idle 24/7 Waste Scenario!)
    for i in range(1, 5):
        resources.append({
            "account_id": dev_acc,
            "region_code": "ap-south-1",
            "service_name": "AmazonEC2",
            "resource_type": "Instance",
            "native_id": f"i-dev-sandbox-t3x-{i:02d}",
            "resource_arn": f"arn:aws:ec2:ap-south-1:333444555666:instance/i-dev-sandbox-t3x-{i:02d}",
            "name": f"dev-sandbox-t3x-{i:02d}",
            "status": "ACTIVE",
            "specs_json": {
                "instance_type": "t3.xlarge",
                "vcpus": 4,
                "memory_gb": 16,
                "running_hours_per_week": 168,
                "observed_off_hours_cpu_pct": 0.8,
            },
            "base_daily_cost": 415.0,  # ~₹12,450/mo each
            "tags": {"Environment": "development", "Team": "devops", "CostCenter": "CC-ENG-202"},
        })

    for i in range(5, 7):
        resources.append({
            "account_id": dev_acc,
            "region_code": "ap-south-1",
            "service_name": "AmazonEC2",
            "resource_type": "Instance",
            "native_id": f"i-dev-sandbox-m5l-{i:02d}",
            "resource_arn": f"arn:aws:ec2:ap-south-1:333444555666:instance/i-dev-sandbox-m5l-{i:02d}",
            "name": f"dev-sandbox-m5l-{i:02d}",
            "status": "ACTIVE",
            "specs_json": {
                "instance_type": "m5.large",
                "vcpus": 2,
                "memory_gb": 8,
                "running_hours_per_week": 168,
                "observed_off_hours_cpu_pct": 0.7,
            },
            "base_daily_cost": 270.0,
            "tags": {"Environment": "development", "Team": "devops", "CostCenter": "CC-ENG-202"},
        })

    # Idle Dev RDS Databases
    for i in range(1, 3):
        resources.append({
            "account_id": dev_acc,
            "region_code": "ap-south-1",
            "service_name": "AmazonRDS",
            "resource_type": "DBInstance",
            "native_id": f"dev-microservice-db-{i:02d}",
            "resource_arn": f"arn:aws:rds:ap-south-1:333444555666:db:dev-microservice-db-{i:02d}",
            "name": f"dev-microservice-db-{i:02d}",
            "status": "ACTIVE",
            "specs_json": {
                "engine": "postgres",
                "instance_class": "db.t3.small",
                "storage_gb": 100,
                "active_client_connections": 0,
                "idle_duration_pct": 88.5,
            },
            "base_daily_cost": 210.0,  # ~₹6,300/mo each
            "tags": {"Environment": "development", "Team": "devops"},
        })

    # 3x Unattached EBS Volumes (Waste Scenario!)
    for i in range(1, 4):
        resources.append({
            "account_id": dev_acc,
            "region_code": "ap-south-1",
            "service_name": "AmazonEC2",
            "resource_type": "Volume",
            "native_id": f"vol-unattached-dev-{i:02d}",
            "resource_arn": f"arn:aws:ec2:ap-south-1:333444555666:volume/vol-unattached-dev-{i:02d}",
            "name": f"orphaned-dev-vol-{i:02d}",
            "status": "AVAILABLE",  # AVAILABLE in AWS means unattached!
            "specs_json": {
                "volume_type": "gp2",
                "size_gb": 400,
                "attachment_state": "detached",
                "volume_status": "AVAILABLE",
                "days_unattached": 18,
            },
            "base_daily_cost": 150.0,  # ~₹4,500/mo each
            "tags": {"Environment": "development", "Team": "devops"},
        })

    # 2x Unassociated Elastic IPs (Waste Scenario!)
    for i in range(1, 3):
        resources.append({
            "account_id": dev_acc,
            "region_code": "ap-south-1",
            "service_name": "AmazonVPC",
            "resource_type": "ElasticIP",
            "native_id": f"eipalloc-orphan-{i:02d}",
            "resource_arn": f"arn:aws:ec2:ap-south-1:333444555666:elastic-ip/eipalloc-orphan-{i:02d}",
            "name": f"idle-eip-{i:02d}",
            "status": "UNASSOCIATED",
            "specs_json": {
                "allocation_id": f"eipalloc-orphan-{i:02d}",
                "association_id": None,
                "association_status": "UNATTACHED",
                "idle_duration_days": 28,
            },
            "base_daily_cost": 35.0,  # ~₹1,050/mo each
            "tags": {"Environment": "development", "Team": "devops"},
        })

    return resources
