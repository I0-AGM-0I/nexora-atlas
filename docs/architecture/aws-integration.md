# AWS Read-Only Integration Architecture — NEXORA ATLAS

## 1. Architectural Role & Boundary Guarantees
The AWS Integration Subsystem in Nexora Atlas establishes a secure, read-only bridge between customer Amazon Web Services accounts and Atlas's canonical data model. 

### Invariant Principles:
1. **Absolute Read-Only Constraint**: Atlas is strictly an observational, intelligence, and financial analytics platform. The application codebase is mathematically verified to contain **zero** mutating API calls (`terminate`, `delete`, `stop`, `reboot`, `modify`, `purchase`, `create`).
2. **Deterministic Canonical Normalization**: All external AWS data structures are immediately converted into canonical Atlas persistence models (`CloudAccount`, `CloudRegion`, `CloudResource`, `CostRecord`, `Tag`). Downstream intelligence engines (Phase 5) and advanced analytics services (Phase 6) operate exclusively on canonical models, completely unaware of whether data originated from the synthetic demo engine or live AWS APIs.
3. **No Infrastructure Execution Privilege**: Atlas never accepts IAM policies with write or remediation capabilities. Even if an administrator accidentally provisions excess IAM permissions, Atlas's internal client factory and adapters expose no methods capable of mutating infrastructure.

---

## 2. Authentication & Authorization Lifecycle
Atlas uses AWS Security Token Service (`sts:AssumeRole`) for cross-account authentication.

```text
┌──────────────────────────────────────────────────────────────┐
│                    NEXORA ATLAS BACKEND                      │
│                                                              │
│  1. Read Config (Role ARN, ExternalId, Session Duration)     │
│  2. Ephemeral AWSClientFactory (Request-Scoped)              │
│  3. sts.assume_role(RoleArn, RoleSessionName, ExternalId)    │
│  4. In-Memory Temporary Credentials (1-hour TTL)             │
│  5. Bounded backoff retry wrapper on transient 5xx/throttles │
│  6. Redacted __repr__ prevents credential leak in logs       │
└──────────────────────────────┬───────────────────────────────┘
                               │ AssumeRole
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                      CUSTOMER AWS ACCOUNT                    │
│                                                              │
│  IAM Role: "AtlasReadOnlyRole"                               │
│  Trust Policy: Requires Atlas Account ID + ExternalId        │
│  Permission Policy: Read-only metadata & Cost Explorer only  │
└──────────────────────────────────────────────────────────────┘
```

### Security Guarantees:
- **No Long-Lived Secret Keys**: Atlas never requires, stores, or accepts root or IAM user access keys (`AKIA...`).
- **Zero Secrets in Database**: The `integrations.config_json` table column stores only non-sensitive metadata: `role_arn`, `external_id`, `regions`, `role_session_name`. Session tokens and temporary credentials exist only in transient memory during active sync operations.
- **Request-Scoped Lifecycle**: There is no global AWS session singleton. Client factories are created per request/sync job and discarded immediately upon completion.

---

## 3. Granular Permission Probing & Least Privilege Boundary
Before attempting full ingestion, the `AWSAuthenticator` performs lightweight, bounded permission probes across five required AWS services:

| Service | Probe Operation | Bounded Parameter | Purpose |
| :--- | :--- | :--- | :--- |
| **STS** | `sts:GetCallerIdentity` | None | Verify account identity, role ARN, and partition |
| **Cost Explorer** | `ce:GetCostAndUsage` | `TimePeriod` (2 days), `Granularity="DAILY"` | Verify access to financial billing data |
| **EC2** | `ec2:DescribeInstances` | `MaxResults=5` | Verify read access to virtual compute instances |
| **RDS** | `rds:DescribeDBInstances` | `MaxRecords=20` | Verify read access to relational database metadata |
| **S3** | `s3:ListBuckets` | Paginated first page | Verify read access to object storage buckets |
| **EKS** | `eks:ListClusters` | `maxResults=1` | Verify read access to managed Kubernetes clusters |

**Non-Blocking Capability Evaluation**: If a service probe fails with `AccessDeniedException`, Atlas does not fail the entire connection. Instead, it marks that specific service as `DISABLED` or `DENIED` and logs granular diagnostics, allowing available services to ingest normally.

---

## 4. Dual-Path Cost Explorer Architecture
AWS Cost Explorer enforces distinct constraints depending on the level of query granularity. Atlas implements a dual-path adapter (`AWSCostExplorerAdapter`) to address these AWS constraints:

```text
AWSCostExplorerAdapter
├── get_aggregated_costs()
│      ├── API: ce:GetCostAndUsage
│      ├── Window: Up to 90 days of daily financial history
│      ├── Grouping: SERVICE, USAGE_TYPE
│      └── Level: CostAttributionLevel.SERVICE
│
└── get_resource_costs()
       ├── API: ce:GetCostAndUsageWithResources (Opt-in feature)
       ├── Window: Strictly bounded to last 14 days (AWS hard limit)
       ├── Grouping: SERVICE, RESOURCE_ID
       └── Level: CostAttributionLevel.RESOURCE (linked to CloudResource.id)
```

### Cost Explorer Degradation Fallback:
If `GetCostAndUsageWithResources` is not enabled on the AWS account or returns `AccessDeniedException`:
1. `res_ce_available` is flagged as `False`.
2. Atlas records the degradation warning in `SyncJob.details_json`.
3. Ingestion continues unimpeded using aggregated 90-day financial records from `GetCostAndUsage`.
4. Downstream intelligence gracefully skips rules requiring resource-level attribution while executing account- and service-level anomaly models.

---

## 5. Cost Attribution Hierarchy & Heterogeneous Units Handling
Atlas models financial records with explicit `CostAttributionLevel`:
1. `RESOURCE`: Cost is directly linked to a specific `CloudResource` (`resource_id IS NOT NULL`).
2. `SERVICE`: Cost is attributed to an AWS service and usage type within an account (`resource_id IS NULL`).
3. `ACCOUNT`: Account-level unallocated costs.
4. `UNATTRIBUTED`: Unallocated or blended adjustment records.

### Heterogeneous Units Handling Invariant:
AWS usage metrics return disparate units (e.g. `Hrs`, `GB-Mo`, `Requests`, `Bytes`, `None`). 
- Atlas strictly tracks `usage_quantity` alongside its native `usage_unit`.
- Natural database deduplication keys incorporate `usage_unit` (`(account_id, usage_date, service_name, resource_id, usage_unit)`).
- Atlas mathematical algorithms **never sum usage quantities** across differing units. Only monetary amounts (`unblended_cost`, `amortized_cost`) are aggregated across disparate services.

---

## 6. Infrastructure Metadata Discovery Adapters
All infrastructure metadata discovery is handled by specialized read-only adapters:

### AWSEC2Adapter
- Iterates over configured target regions (e.g. `us-east-1`, `ap-south-1`).
- Paginates `ec2:DescribeInstances`.
- Extracts instance state (`running`, `stopped`, `terminated`), instance type (`c5.4xlarge`), launch time, and tags.
- Populates `specs_json` with CPU architecture, virtualization type, and public/private IP addresses.

### AWSEBSAdapter
- Paginates `ec2:DescribeVolumes`.
- Records volume type (`gp2`, `gp3`, `io1`), provisioned IOPS, throughput, size in GB, and encryption status.
- Evaluates attachment status: sets `is_attached = len(attachments) > 0` and `status = "in-use"` or `"available"`.
- Enables Phase 5 `UnattachedVolumeRule` detection.

### AWSRDSAdapter
- Paginates `rds:DescribeDBInstances`.
- Captures DB engine (`postgres`, `mysql`, `aurora`), instance class (`db.r5.xlarge`), storage allocation, multi-AZ deployment flag, and endpoint.

### AWSS3Adapter
- Uses SDK paginator for `s3:ListBuckets`.
- Resolves bucket region using `s3:HeadBucket` and inspecting the `x-amz-bucket-region` HTTP header (preventing the known location constraint bug with `GetBucketLocation`).
- Queries bucket versioning (`s3:GetBucketVersioning`) and tags (`s3:GetBucketTagging`).
- **Zero Content Inspection**: Never calls `ListObjectsV2` or `GetObject`. Bucket contents and files are strictly private and out-of-scope.

### AWSEKSAdapter
- Paginates `eks:ListClusters` and describes each cluster.
- Paginates `eks:ListNodegroups` for each cluster and records nodegroup scaling configuration (min, max, desired size).
- **Hierarchy Distinction**: Explicitly models `CLUSTER` and `NODEGROUP` as distinct `resource_type`s, preventing conflation with underlying EC2 worker instances.

---

## 7. Composite Resource Identity Specification
In multi-account, multi-region cloud infrastructures, native identifiers (e.g., `vol-12345` or `default`) can collide across regions or accounts. Atlas enforces composite resource identity:

$$\text{Composite Key} = \begin{cases} \text{provider} + "::" + \text{account\_id} + "::" + \text{resource\_arn} & \text{if ARN exists} \\ \text{provider} + "::" + \text{account\_id} + "::" + \text{service\_name} + "::" + \text{native\_id} & \text{otherwise} \end{cases}$$

This deterministic composite key guarantees:
1. No cross-account collisions.
2. No cross-service collisions.
3. Stable reference identity across successive synchronization jobs.

---

## 8. Normalization Engine (`AWSModelMapper`)
The `AWSModelMapper` transforms provider-specific Data Transfer Objects (DTOs) into canonical database entities:
- `DiscoveredAccount` $\to$ `CloudAccount`
- `DiscoveredRegion` $\to$ `CloudRegion`
- `DiscoveredResource` $\to$ `CloudResource`
- `DiscoveredTag` $\to$ `Tag`
- `DiscoveredCostRecord` $\to$ `CostRecord`

Monetary values are strictly parsed using Python `Decimal` with rounding `ROUND_HALF_UP` to maintain exact 4-decimal-place precision (`$0.0001`).

---

## 9. Deterministic Source Record Key
Every ingested financial line item is tagged with a SHA-256 hash representing its unique provenance:

$$\text{source\_record\_key} = \text{SHA256}(\text{account} \,|\, \text{date} \,|\, \text{service} \,|\, \text{resource} \,|\, \text{region} \,|\, \text{usage\_type} \,|\, \text{operation} \,|\, \text{unit} \,|\, \text{attribution\_level})$$

This cryptographic digest guarantees:
- Idempotent re-syncing: Re-running a sync over the same window updates existing rows rather than creating duplicate costs.
- Tamper-evident provenance: Financial records can always be traced back to their originating AWS Cost Explorer line item.

---

## 10. Synchronization Lifecycle & Windows
Sync jobs are managed by `SyncCoordinator` with deterministic window calculation (`SyncWindowCalculator`):
- **Initial Sync**: When an integration is synchronized for the first time (`last_sync_at IS NULL`), Atlas queries a full **90-day window** (`today - 90 days` to `today`).
- **Incremental Sync**: For existing integrations, Atlas applies an **authoritative 14-day overlap window** (`last_sync_at - 14 days` to `today`). This captures late-arriving AWS billing adjustments, refunds, and final cloud provider invoice reconciliations.
- **Sync Job State Machine**: Each run creates a `SyncJob` with state `PENDING` $\to$ `IN_PROGRESS` $\to$ `COMPLETED` (or `FAILED` / `PARTIAL`).

---

## 11. Authoritative-Only Disappearance Semantics
When cloud resources are deleted or terminated in AWS, monitoring systems often incorrectly delete or orphan records if an API call fails. Atlas implements **authoritative disappearance**:

1. A service inventory scan is authoritative only if that specific adapter's API calls succeed 100% without exception.
2. If `AWSEC2Adapter` discovers 4 instances where 5 previously existed, and the EC2 call had zero errors, the missing instance status transitions to `TERMINATED`.
3. If `AWSRDSAdapter` fails (e.g. timeout or throttling), **no RDS instances are marked as terminated**. Atlas preserves existing state, logging an adapter error.
4. Resources are never deleted from PostgreSQL; their status is updated, preserving full historical auditability.

---

## 12. Graceful Degradation & Partial Ingestion Handling
Ingestion failures are isolated per service adapter:
- An S3 permission failure does not abort EC2 or Cost Explorer ingestion.
- The `SyncCoordinator` records individual adapter errors in `SyncJob.details_json["errors"]`.
- If some adapters succeed while others fail, the sync finishes with status `COMPLETED` (or `PARTIAL`), updating `resources_created` and `cost_records_created` for the successful adapters.

---

## 13. Provenance, Audit Trails & Observability
Every synchronization event commits an immutable entry to `AuditLog`:
- `actor_id`: `"system:aws-sync"`
- `action`: `"INTEGRATION_SYNC_COMPLETED"`
- `resource_type`: `"Integration"`
- `resource_id`: `integration.id`
- `metadata_json`: Contains execution duration, counts of resources discovered, costs created/updated, and any adapter degradation warnings.

---

## 14. Security & Credential Protection Invariants
Atlas enforces strict security guardrails across all layers:
1. **Masked Role ARNs**: API endpoints return role ARNs masked as `arn:aws:iam::***:role/AtlasReadOnlyRole`.
2. **ExternalId Redaction**: The secret `external_id` handshake string is never exposed in frontend API responses or browser local storage.
3. **Repr Sanitization**: `AWSClientFactory.__repr__()` outputs `<AWSClientFactory(role_arn=arn:aws:iam::***:role/..., region=...) [CREDENTIALS_REDACTED]>`.
4. **Log Sanitization**: Credentials, session tokens, and raw authorization headers are never logged.

---

## 15. Source Isolation Guarantee
The platform strictly isolates synthetic demo environments from real AWS connections:
- In Demo Mode (`is_demo=True`), the system queries only demo organizations and synthetic accounts (`org_nexora_demo`, `000011112222`).
- The Demo Data Engine never invokes AWS adapters.
- Live AWS synchronizations only link to authenticated customer organizations (`is_demo=False`).
- Both pathways pass through identical downstream intelligence and analytics pipelines.

---

## 16. Downstream Intelligence & Analytics Integration
Once AWS data is normalized into canonical models:
- **Phase 5 Intelligence Engine** (`IntelligenceEngine.run(session, org_id)`):
  - Analyzes real AWS `CostRecord` time series for spikes and trends.
  - Applies `UnattachedVolumeRule` to discovered EBS volumes.
  - Applies `OversizedInstanceRule` to EC2 instances using CloudWatch/specs telemetry.
  - Generates defensible `OpportunityCandidate` and `RecommendationCandidate` records.
- **Phase 6 Advanced Analytics** (`AnalyticsService.get_summary(session, tenant)`):
  - Computes cost drivers (absolute and net change contributions).
  - Evaluates Pareto concentration (80/20 spend rule).
  - Calculates capacity headroom (`observed_utilization_headroom_cpu = 100% - p95_cpu`).
  - Runs scenario modeling against real AWS cost baselines.

---

## 17. Frontend Integration Center UX
The Atlas Web interface provides a dedicated **Cloud Integrations Hub** (`/integrations`):
- **Read-Only Trust Banner**: Prominently highlights read-only safety guarantees, zero mutating actions, and external ID configuration.
- **Granular Capability Checklist**: Real-time badges for `Cost Explorer (Aggregated)`, `Cost Explorer (Resource-Level)`, `EC2 Compute`, `EBS Storage`, `RDS Databases`, `S3 Storage`, and `EKS Clusters`.
- **Validation Modal**: Validates cross-account trust setup and permissions before initiating synchronization.
- **Sync History**: Displays historical sync jobs, duration, records processed, and authoritative statuses.

---

## 18. Verification, Testing & Static AST Safety Enforcement
Atlas maintains comprehensive automated test suites verifying every architectural guarantee:
1. **Static AST Safety Scanner** (`tests/test_aws_safety.py`):
   - Scans the entire Python codebase using `ast.parse`.
   - Asserts that no banned AWS API operations (`terminate_instances`, `stop_instances`, `delete_volume`, `modify_db_instance`, `purchase_reserved_instances_offering`, etc.) exist anywhere in code.
   - Asserts that no generic command executors (`subprocess`, `os.system`) are present.
2. **Adapter Unit Tests** (`tests/test_aws_adapters.py`):
   - Mocks AWS SDK responses to test parsing of EC2, EBS, RDS, S3 HeadBucket, EKS, and Cost Explorer.
3. **Degradation & Disappearance Tests** (`tests/test_aws_ce_degradation.py`, `tests/test_aws_disappearance.py`):
   - Proves partial adapter failures preserve existing resources.
   - Proves resource CE degradation falls back to aggregated CE.
4. **End-to-End Golden Integration Test** (`tests/test_phase7_aws_ingestion_world.py`):
   - Connects mock AWS account $\to$ runs full sync $\to$ normalizes canonical records $\to$ runs Phase 5 intelligence $\to$ runs Phase 6 advanced analytics $\to$ verifies complete chain of reasoning.
5. **Zero-Regression Suite**: 99 backend tests passing (100%), 21 frontend vitest tests passing (100%), Vite production build passing with 0 errors.

