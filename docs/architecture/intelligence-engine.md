# NEXORA ATLAS — Phase 5: Intelligence Engine Architecture

## 1. Executive Summary

Phase 5 establishes the deterministic, mathematical intelligence core of NEXORA ATLAS.

The engine transforms raw financial line items and operational telemetry into actionable, auditable, evidence-backed optimization decisions without relying on non-deterministic LLMs or external cloud APIs.

```text
COST DATA (Financial Telemetry)
    ↓
BASELINE (Rolling Mean, Median, MAD)
    ↓
DEVIATION (Delta & Percentage Change)
    ↓
ANOMALY (Rules A, B, C, D)
    ↓
EVIDENCE CONTRACTS (Telemetry Verification & Gating)
    ↓
WASTE DETECTION (Rules 1 - 7 with Explicit Assumptions)
    ↓
RECOMMENDATIONS (Multi-Option Tradeoffs & Action Plans)
    ↓
SAVINGS + RISK (Reconciled INR Amounts & Operational Blast Radius)
```

---

## 2. Core Architectural Guarantees

### 2.1 AWS Safety Rule: 100% Offline Execution
* The intelligence pipeline operates entirely in-memory and against the persistent relational database.
* Zero network connections to AWS endpoints.
* Zero boto3 SDK calls.
* Zero AWS credential requirements.
* Analysis operation only: **Zero cloud infrastructure mutation or deletion.**

### 2.2 Mathematical Precision & Monetary Integrity
* All currency amounts are computed and stored using pure Python `Decimal` with 4 decimal places (`Numeric(18, 4)`).
* Zero IEEE 754 floating-point numbers are used for monetary accumulation.
* Mathematical reconciliation is guaranteed: $\text{Annual Savings} \equiv \text{Monthly Savings} \times 12$.

### 2.3 Strict Evidence Contracts & No Phantom Telemetry
* Telemetry sources are decoupled: financial telemetry (`CostRecord`) is strictly separated from operational telemetry (`CloudResource.specs_json`).
* Every detection rule declares an explicit `EvidenceContract`:
  ```python
  class EvidenceContract(BaseModel):
      rule_name: str
      required_fields: List[str]
      min_sample_size: int = 1
      telemetry_source: str = "operational"
  ```
* If required operational telemetry is absent:
  * Rule status evaluates to `RuleStatus.SKIPPED`.
  * An explicit, auditable skip reason is recorded (e.g. `Missing required operational telemetry field: p95_cpu_utilization_pct`).
  * Findings count is `0`.
  * The engine never manufactures or hallucinates telemetry.

### 2.4 Idempotency & Provenance
* Every execution is tagged with a unique `run_id` (e.g., `intel-run-6ef428678a96`) and canonical `ruleset_version = "atlas-intelligence-v1"`.
* Persistence is idempotent: executing the engine multiple times against identical telemetry produces **zero duplicate records** in `anomalies`, `optimization_opportunities`, or `recommendations`.
* Every pipeline run logs an immutable governance entry in `audit_logs`.

---

## 3. Statistical Baseline Engine

Located in [`apps/api/app/intelligence/baseline/calculator.py`](file:///d:/Nexora%20Atlas/apps/api/app/intelligence/baseline/calculator.py).

### 3.1 Supported Estimators
1. **Rolling Mean**: Sample mean over the historical baseline window (default 14 days).
2. **Rolling Median**: Center value of sorted cost distribution, robust against historical spikes.
3. **Median Absolute Deviation (MAD)**:
   $$\text{MAD} = \text{median}(|x_i - \text{median}(X)|)$$
   Serves as the primary dispersion estimator for cross-sectional anomaly detection.
4. **Standard Deviation**: Sample standard deviation ($\sqrt{s^2}$) with Bessel's correction ($n-1$).

### 3.2 Sample Sufficiency Gating
* Baseline requires $\ge 3$ valid historical observations.
* If sample size is insufficient, `is_sufficient = False` and baseline value defaults to `0.0000`, skipping dependent rules safely.

---

## 4. Anomaly Detection Engine

Located in [`apps/api/app/intelligence/anomaly/`](file:///d:/Nexora%20Atlas/apps/api/app/intelligence/anomaly/).

| Rule ID | Rule Name | Condition | Gating Contract |
| :--- | :--- | :--- | :--- |
| `ANOM-RULE-A-COST-SPIKE` | Cost Spike | Single-day spend $\ge 20\%$ above 14-day baseline and $\Delta > 0$ | $n \ge 4$ cost records |
| `ANOM-RULE-B-SUSTAINED-INCREASE` | Sustained Increase | Spend elevated $\ge 15\%$ for $\ge 3$ consecutive days | $n \ge 6$ cost records |
| `ANOM-RULE-C-RESOURCE-OUTLIER` | Resource Outlier | Resource spend $> \text{median} + 2.5 \times \text{MAD}$ within peer cohort | Cohort population $n \ge 4$ |
| `ANOM-RULE-D-ACCOUNT-SHIFT` | Account Shift | Account share of org spend shifts by $\ge 10\%$ and $\Delta \ge ₹10,000$ | Current & prev 30d spend |

### 4.1 MAD Robustness & Zero Division Safeguard
When all resources in a cohort exhibit identical spend ($\text{MAD} = 0$), the outlier rule falls back to verifying whether candidate spend exceeds the median by $\ge 25\%$ and absolute difference $\ge ₹1,000$.

### 4.2 Context-Aware Severity Scoring
Combines:
* Absolute magnitude in INR ($< 2k$, $10k$, $30k$, $\ge 1\text{ Lakh}$)
* Percentage deviation ($20\%$, $30\%$, $\ge 50\%$)
* Duration (single-day vs sustained)
* Environment multiplier ($1.3\times$ for Production, $0.8\times$ for Dev/Sandbox)

---

## 5. Waste Detection & Optimization Opportunities

Located in [`apps/api/app/intelligence/waste/`](file:///d:/Nexora%20Atlas/apps/api/app/intelligence/waste/).

| Rule | Target Resource | Evidence Fields | Detection Threshold | Action Blueprint |
| :--- | :--- | :--- | :--- | :--- |
| **Unattached Volume** | EBS Volume | `volume_status`, `days_unattached` | Status `AVAILABLE` & days $\ge 7$ | Snapshot & delete detached volume |
| **Oversized Instance** | EC2 Compute | `p95_cpu_utilization_pct`, `instance_type` | `p95_cpu < 20%` on large tier | Downsize in-family + Graviton option |
| **Off-Hours Idle** | Non-Prod EC2 | `running_hours_per_week`, `observed_off_hours_cpu_pct` | Running 168 hrs/wk & off-hours CPU $< 2\%$ | Schedule Mon-Fri 09:00-18:00 IST |
| **Idle Database** | RDS Database | `active_client_connections`, `idle_duration_pct` | Connections $\le 1$ & idle duration $\ge 80\%$ | Pause instance; snapshot retention |
| **Legacy Storage Tier**| EBS Storage | `volume_type` | Type is `gp2` | Zero-downtime migration to `gp3` (20% savings) |
| **Unassociated EIP** | VPC Elastic IP | `idle_duration_days` | Unattached for $\ge 7$ days | Release Elastic IP to pool |
| **Unmanaged Versions** | S3 Bucket | `non_current_versions_gb`, `lifecycle_rules_found` | Non-current $\ge 1000\text{ GB}$ & 0 lifecycle rules | Expiration & Glacier IR tiering |

---

## 6. Recommendation Engine & Tradeoff Modeling

Located in [`apps/api/app/intelligence/recommendation/`](file:///d:/Nexora%20Atlas/apps/api/app/intelligence/recommendation/).

* **No Forced Option Parity**: Straightforward waste (unattached storage, unassociated EIP) produces a single definitive recommendation. Complex infrastructure changes produce multiple tradeoff options:
  * Option 1 (In-family downsize): e.g. `m5.4xlarge -> m5.large` (Low risk).
  * Option 2 (Modernization): e.g. `m5.4xlarge -> c7g.xlarge` ARM64 Graviton (Higher savings, Medium risk requiring container validation).
* **Risk Categorization**:
  * `NONE`: In-place tiering (`gp2 -> gp3`), releasing unused IP.
  * `LOW`: Non-production modifications, automated schedules.
  * `MEDIUM`: Production architecture shifts (x86 to ARM64), downsizing with rollback plan.
  * `HIGH`: Destructive production teardowns without rollback plan.

---

## 7. Evidence Lineage & Auditability

Every finding maintains a complete, verifiable audit trail:

$$\text{Finding} \to \text{Resource ID} \to \text{Historical Cost Records} \to \text{Baseline Window} \to \text{Deviation} \to \text{Evidence Facts} \to \text{Action Plan}$$

This lineage was independently verified in the **Crown Jewel Test** ([`test_crown_jewel_intelligence_rediscovery`](file:///d:/Nexora%20Atlas/apps/api/tests/test_intelligence_rediscovery.py)), where the engine successfully rediscovered the simulated GPU surge, detached EBS storage, and oversized EKS compute without hardcoded names or pre-arranged answers.
