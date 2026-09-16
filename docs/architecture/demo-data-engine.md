# Demo Data Engine Architecture - NEXORA ATLAS (Phase 3)

## 1. Executive Overview & Purpose

The **NEXORA ATLAS Demo Data Engine** produces an enterprise-grade, deterministic, and relationally coherent synthetic cloud environment. 

Rather than generating disconnected fake database rows, the engine constructs a single unified reality where:
```
Discovered Resources ➔ Daily Cost Records ➔ Periodic Snapshots ➔ Statistical Anomalies
        │                                                                │
        ▼                                                                ▼
Operational Evidence ➔ Waste Opportunities ➔ Concrete Recommendations ➔ Scenario Simulations
```
Every visual metric on the ATLAS Overview Dashboard, Spend Explorer, Anomaly Center, and Optimization Center traces back to empirical database rows with 100% mathematical reconciliation.

---

## 2. Absolute Safety Boundary: 100% Offline
- **Zero AWS Connectivity**: The Demo Data Engine does not invoke `boto3`, execute HTTP requests, inspect AWS environment variables, or attempt credential resolution.
- **Simulated Accounts**: All accounts and resources are synthetic entities flagged with `is_demo = True`.
- **Execution Mode**: Operates exclusively when `DEMO_MODE=true`.

---

## 3. Synthetic Organization Identity
- **Legal Entity**: **Nexora Labs Inc**
- **Slug**: `nexora-labs`
- **Currency**: `INR` (Indian Rupee, formatted in Lakhs ₹L and Crores ₹Cr)
- **Timezone**: `Asia/Kolkata` (IST, UTC+5:30)
- **Monthly Run Rate**: **₹21.4 Lakhs / month** (~$25,700 USD/month)
- **Profile**: B2B SaaS company delivering real-time telemetry processing, customer analytics, and AI/ML inference pipelines.

---

## 4. Cloud Account Topology

Three segregated accounts partition production, staging, and development workloads:

| Account Name | Account ID | Environment | Description | Target Monthly Spend |
|---|---|---|---|---|
| **Production Core** | `111222333444` | Production | High-availability API services, primary databases, customer analytics, GPU inference | ~₹15.8L (73.8%) |
| **Staging Workloads** | `222333444555` | Staging | Pre-release staging clusters, integration testing | ~₹2.6L (12.1%) |
| **Development & Sandbox** | `333444555666` | Development | Engineering sandboxes, CI/CD runners, experimental workloads | ~₹3.0L (14.0%) |

---

## 5. Normalized Geographic Regions

1. **`ap-south-1` (Mumbai)**: Primary production and customer traffic.
2. **`us-east-1` (N. Virginia)**: AI model training/inference and global external endpoints.
3. **`us-west-2` (Oregon)**: Secondary analytics clusters and disaster recovery.
4. **`eu-west-1` (Ireland)**: European edge caches and compliance backups.

---

## 6. Resource Topology & Workload Stories

The inventory contains **72 first-class cloud resources** organized into distinct workload stories:

### A. Production Web & API Tier (`ap-south-1`)
- 2 Application Load Balancers (`alb-prod-external`, `alb-prod-internal`)
- 8 EC2 Instances: `prod-api-01..04` (`m5.2xlarge`), `prod-worker-01..04` (`c5.2xlarge`)
- 1 Multi-AZ Aurora PostgreSQL Database: `prod-db-primary` (`db.r5.2xlarge`) + `prod-db-replica` (`db.r5.2xlarge`)
- 1 ElastiCache Redis Cluster (`cache.r5.large`, 3 nodes)
- Attached EBS `gp3` volumes (4 x 500 GB)
- 2 NAT Gateways (`nat-gw-prod-az1`, `nat-gw-prod-az2`)

### B. Analytics & Big Data Platform (`us-west-2`)
- 1 EKS Kubernetes Cluster (`analytics-eks-cluster`) with 6 Node Workers (`m5.4xlarge`) — *Oversized waste scenario!*
- 3 S3 Buckets: `nexora-raw-data-lake`, `nexora-analytics-warehouse`, `nexora-emr-scratch` — *Storage accumulation scenario!*
- 1 EMR Spark Cluster (`emr-batch-processor`)
- 2 Attached EBS volumes (`gp2`, 1000 GB each) — *gp2 to gp3 migration opportunity!*

### C. AI / Machine Learning Inference Service (`us-east-1`)
- 3 GPU Instances: `ml-inference-g4dn-01..03` (`g4dn.2xlarge`) — *Traffic spike anomaly scenario!*
- 1 S3 Model Registry: `nexora-ml-model-registry`

### D. Staging Environment (`ap-south-1`)
- 1 ALB (`alb-staging`)
- 4 EC2 Instances (`t3.large`)
- 1 RDS PostgreSQL Database (`db.t3.medium`)
- 1 S3 Bucket (`nexora-staging-assets`)

### E. Development & Engineering Sandbox (`ap-south-1`)
- 6 EC2 Instances: `dev-sandbox-01..06` (`t3.xlarge`, `m5.large`) — *Idle overnight & weekend waste scenario!*
- 2 RDS Databases: `dev-microservice-db-01..02` (`db.t3.small`) — *Idle database waste scenario!*
- 3 Unattached EBS Volumes: `vol-unattached-dev-01..03` (in `available` state) — *Unattached volume waste scenario!*
- 2 Unassociated Elastic IPs: `eip-orphan-01..02` — *Idle network waste scenario!*

### F. Global Networking & CDN
- 1 CloudFront Distribution (`d123456abcdef8`)
- Global Data Transfer Out line items

---

## 7. Tagging Taxonomy
Every resource carries standardized organizational metadata with strict single-key uniqueness:
- `Environment`: `production` | `staging` | `development`
- `Team`: `platform` | `core-api` | `analytics` | `ml` | `devops`
- `Application`: `api-gateway` | `customer-data-platform` | `model-server` | `internal-tools`
- `Owner`: `platform-engineering@nexora.io` | `ml-infra@nexora.io`
- `CostCenter`: `CC-PROD-101` | `CC-ENG-202` | `CC-AI-303`

---

## 8. 90-Day Deterministic Cost Generation Methodology

- **Seed**: `DEMO_SEED = 424242`.
- **Timeframe**: 90 days of daily cost records (yielding ~6,480 granular `CostRecord` entries).
- **Formula**:
  $$\text{DailyCost}(r, d) = \text{BaseRate}(r) \times \text{DOWFactor}(d) \times \text{GrowthFactor}(d) + \text{EventDelta}(r, d)$$
- **Day-of-Week (DOW) Modulation**:
  - Production workloads: ±2% normal business variation.
  - Development environments: Drops by 60% on Saturdays and Sundays (unless experiencing the "idle dev environment" waste rule).
  - Analytics batch jobs: Systematic spikes on Tuesdays and Thursdays.
- **Intentional Controlled Events**:
  1. *Day 1–90*: S3 Storage grows linearly from ₹1.17L to ₹1.45L (+24%) due to lack of lifecycle expiration rules.
  2. *Day 65–90*: AI GPU inference adoption expands, driving GPU compute from ₹1.25L to ₹1.90L (+52%).
  3. *Day 75–85*: Core API unoptimized query surge causes EC2 auto-scaling spike from ₹3.4L to ₹4.7L (+38%).
  4. *Day 80–83*: Staging data transfer test spike (+65%).

---

## 9. Financial Consistency & Reconciliation Guarantee

Every aggregate financial metric satisfies mathematical closure:
1. $\sum_{\text{accounts}} \text{Cost} = \text{Organization Total}$
2. $\sum_{\text{services}} \text{Cost} = \text{Account Total}$
3. $\sum_{\text{days in month}} \text{CostRecord.unblended\_cost} = \text{CostSnapshot.total\_cost}$
4. $\text{CostSnapshot.breakdown\_json}[s] = \sum_{\text{records in } s} \text{CostRecord.unblended\_cost}$

---

## 10. Synthetic Operational Telemetry Layer
Decoupled from financial records, the demo engine synthesizes empirical utilization snapshots stored in `OptimizationOpportunity.evidence_json` and `Recommendation.evidence_json`:
- Analytics EKS worker nodes: Observed p95 CPU: 11.2%, p95 Memory: 18.4%.
- Development EC2 instances: Observed CPU < 2.5% between 18:00 and 09:00 IST and all weekend hours.
- Dev RDS databases: 0 active connections for > 88% of elapsed hours.

---

## 11. Concrete Anomaly Scenarios

| Anomaly Key | Target Service / Cluster | Observed Cost | Baseline Cost | Change | Severity | Confidence | Detection Rule |
|---|---|---|---|---|---|---|---|
| **ANOM-01** | `AmazonEC2` (Production API) | ₹4,70,000 | ₹3,40,000 | +38.2% | **HIGH** | 91.5% | `ROLLING_ZSCORE_EXCEEDED` |
| **ANOM-02** | `AmazonEC2` (GPU AI Inference) | ₹1,90,000 | ₹1,25,000 | +52.0% | **HIGH** | 88.0% | `SUDDEN_SPIKE_DETECTED` |
| **ANOM-03** | `AmazonS3` (Data Lake Accumulation) | ₹1,45,000 | ₹1,17,000 | +23.9% | **MEDIUM** | 84.0% | `HISTORICAL_GROWTH_VIOLATION` |
| **ANOM-04** | `AWSDataTransfer` (Staging Egress) | ₹38,000 | ₹23,000 | +65.2% | **LOW** | 79.5% | `THRESHOLD_MULTIPLIER_2X` |

---

## 12. Waste Detection & Actionable Recommendations

**Total Identifiable Monthly Savings**: **₹4,60,000 / month** (₹4.6 Lakhs/month)  
**Total Annual Savings**: **₹55,20,000 / year** (₹55.2 Lakhs/year)

| # | Opportunity Category | Inefficiency Detected | Recommended Action | Monthly Savings | Annual Savings | Risk | Confidence |
|---|---|---|---|---|---|---|---|
| 1 | **COMPUTE** | Analytics EKS 6x m5.4xlarge nodes underutilized (p95 CPU 11%) | Downsize to `m5.large` | **₹1,42,000** | ₹17,04,000 | LOW | 94% |
| 2 | **COMPUTE** | Analytics EKS alternative proposal | Migrate to Graviton `c7g.xlarge` | **₹1,65,000** | ₹19,80,000 | MEDIUM | 82% |
| 3 | **COMPUTE** | Dev sandbox instances running 24/7 | Auto-stop outside 09:00–18:00 IST | **₹92,000** | ₹11,04,000 | LOW | 96% |
| 4 | **DATABASE** | Dev RDS clusters with zero active connections | Snapshot & stop idle instances | **₹38,000** | ₹4,56,000 | LOW | 92% |
| 5 | **STORAGE** | 3 unattached EBS volumes in `available` state > 14 days | Snapshot and terminate | **₹18,000** | ₹2,16,000 | LOW | 99% |
| 6 | **STORAGE** | Analytics EBS volumes on legacy `gp2` | Convert to modern `gp3` | **₹26,000** | ₹3,12,000 | NONE | 98% |
| 7 | **NETWORKING** | 2 unassociated Elastic IPs | Release unallocated IPs | **₹4,000** | ₹48,000 | NONE | 100% |
| 8 | **STORAGE** | Obsolete S3 non-current versions without lifecycle rules | Configure 30-day expiration & Glacier tiering | **₹1,40,000** | ₹16,80,000 | LOW | 89% |

*(Note: In Optimization Center, default active savings aggregation sums the primary recommendation per opportunity: 142k + 92k + 38k + 18k + 26k + 4k + 140k = **₹4,60,000/mo**).*

---

## 13. Simulated Scenarios & Trade-off Matrix

- **Baseline Run-Rate**: **₹21,40,000 / month**

| Scenario Name | Description | Projected Run Rate | Monthly Savings | % Savings | Perf Risk | Rel Risk | Complexity |
|---|---|---|---|---|---|---|---|
| **Option A: Conservative** | Non-disruptive dev scheduling, unattached EBS cleanup, gp2 to gp3 | **₹18,90,000** | ₹2,50,000 | 11.68% | None | None | Low |
| **Option B: Balanced** | Option A + S3 lifecycle tiering + Dev RDS shutdown | **₹17,70,000** | ₹3,70,000 | 17.29% | Low | Low | Medium |
| **Option C: Aggressive** | Option B + EKS node right-sizing to m5.large | **₹16,80,000** | ₹4,60,000 | 21.50% | Low | Medium | Medium |

All scenarios guarantee:
$$\text{monthly\_savings} = \text{baseline} - \text{projected}$$
$$\text{pct\_savings} = \frac{\text{monthly\_savings}}{\text{baseline}} \times 100$$

---

## 14. Forward Forecast Projections
Extrapolating 90-day trajectory forward 3 months (marked with `algorithm = "demo_fixture"`):
- Month +1: Projected **₹23,80,000** (Range: ₹22.4L – ₹25.2L, 88% confidence)
- Month +2: Projected **₹26,50,000** (Range: ₹24.8L – ₹28.2L, 85% confidence)
- Month +3: Projected **₹31,40,000** (Range: ₹29.1L – ₹33.7L, 82% confidence)
- Drivers: `AmazonEC2` (42%), `GPU/AI Workloads` (28%), `AmazonRDS` (18%), `AmazonS3` (12%).

---

## 15. Reset & Reseed Strategy
- Target: `Organization.is_demo == True` (`nexora-labs`).
- Cascade: Removing the demo organization cleanly triggers database cascade deletion of all child accounts, resources, cost records, snapshots, anomalies, recommendations, and scenarios.
- Idempotency: `seed_demo_data(reset_first=True)` safely resets and regenerates the exact identical dataset.
