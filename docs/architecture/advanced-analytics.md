# NEXORA ATLAS — Phase 6: Advanced Analytics & Optimization Modeling Architecture

## 1. Executive Summary

Phase 6 elevates NEXORA ATLAS from deterministic problem detection (Phase 5) to **deep analytical reasoning, structural attribution, and architectural simulation**.

Where Phase 5 answered:
> *"What is anomalous, inefficient, or wasteful right now?"*

Phase 6 answers:
> *"Why did our spend change, which exact dimensions drove the change, how concentrated is our cloud footprint, what is our headroom, and what happens to cost, risk, and architecture if we simulate changes?"*

The system implements a seamless **Progressive Chain of Reasoning**:
```text
DASHBOARD (Executive KPI Rollup)
    ↓
SPEND EXPLORER (Historical Trend & Regime Decomposition)
    ↓
COST DRIVER ANALYSIS (Dimension Attribution & Dual Contribution Metrics)
    ↓
OPTIMIZATION OPPORTUNITIES (Evidence-Gated Waste Findings)
    ↓
SCENARIOS & PORTFOLIO (Interactive Architecture Workbench & Conflict Detection)
```

---

## 2. Core Architectural Guarantees & Non-Negotiables

### 2.1 100% Offline Execution & AWS Safety Rule
* Zero outbound connections to AWS, cloud providers, or third-party APIs.
* Zero AWS credential requirements.
* Zero live infrastructure mutations or autonomous changes.
* Operates strictly against the relational persistence layer and in-memory analytical engines.

### 2.2 Deterministic Mathematics & Zero Non-Deterministic LLMs
* All calculations are deterministic, reproducible, and verifiable.
* Zero probabilistic hallucination or non-reproducible text generation in analytical pipelines.
* Strict evidence gating: if telemetry is absent, status is marked `INSUFFICIENT_DATA` or `NOT_CONFIGURED` without manufacturing phantom metrics.

### 2.3 Pure Decimal Financial Precision & Exact Invariants
* All monetary calculations use Python `Decimal` with 4 fractional digits (`Numeric(18, 4)`).
* Financial invariants are strictly enforced:
  $$\sum \Delta_{\text{services}} = \Delta_{\text{total}}$$
  $$\sum \Delta_{\text{accounts}} = \Delta_{\text{total}}$$
  $$\sum \Delta_{\text{regions}} = \Delta_{\text{total}}$$
  $$\text{Baseline Cost} - \text{Projected Cost} = \text{Monthly Savings}$$
  $$\text{Annual Savings} = \text{Monthly Savings} \times 12$$

---

## 3. Trends & Regime Decomposition

The trend engine (`apps/api/app/analytics/trends/`) decomposes daily spend series over configurable rolling windows (7d, 14d, 30d, 90d).

### 3.1 Deterministic Trend Direction Precedence
Trend direction is classified using strict precedence:
1. **`VOLATILE`**: If the coefficient of variation ($CV = \frac{\sigma}{\mu}$) exceeds $0.25$ ($25\%$), the series is classified as `VOLATILE` regardless of net slope.
2. **`INCREASING`**: If $CV < 0.25$ and period-over-period percentage delta $> +3.0\%$.
3. **`DECREASING`**: If $CV < 0.25$ and period-over-period percentage delta $< -3.0\%$.
4. **`STABLE`**: If $CV < 0.25$ and $-3.0\% \le \text{delta} \le +3.0\%$.

### 3.2 Regime Classification Precedence
Operational spend behavior is categorized into four distinct behavioral regimes with deterministic precedence:
1. **`SPIKE`**: Current spend exceeds the baseline mean by $> 50\%$ on that single day ($Z > 3.0$).
2. **`RECOVERY`**: A previous `SPIKE` occurred within the last 7 days, and spend is strictly decreasing towards baseline ($c_t < c_{t-1}$).
3. **`ELEVATED`**: Daily spend exceeds the baseline mean by $> 10\%$ for 3 or more consecutive days without meeting the single-day extreme spike criterion.
4. **`NORMAL`**: Spend fluctuates within standard operational baseline variance ($\pm 10\%$).

---

## 4. Cost Driver Attribution & Dual Contribution Metrics

When total spend shifts between periods, the driver attribution engine (`apps/api/app/analytics/drivers/`) isolates the root cause across four orthogonal dimensions:
- **Service** (e.g., AmazonEC2, AmazonRDS, AmazonS3)
- **Account** (e.g., Production, Staging, Data Engineering)
- **Resource** (e.g., `prod-primary-db`, `data-lake-cluster`)
- **Region** (e.g., `ap-south-1`, `us-east-1`, `global`)

### 4.1 Dual Contribution Metrics
To eliminate ambiguity when positive and negative deltas offset each other, Atlas calculates two distinct, non-conflated contribution metrics:

1. **Absolute Contribution Percentage**:
   $$\text{absolute\_contribution\_pct} = \frac{|\Delta_i|}{\sum_{j} |\Delta_j|} \times 100$$
   *Measures the share of total volatility/activity accounted for by this driver. Always positive and sums to 100%.*

2. **Net Change Contribution Percentage**:
   $$\text{net\_change\_contribution\_pct} = \frac{\Delta_i}{\Delta_{\text{total}}} \times 100 \quad (\text{for } \Delta_{\text{total}} \ne 0)$$
   *Measures the proportion of net portfolio shift explained by this driver. Handles offsets (can exceed 100% or be negative if opposing forces exist).*

### 4.2 Change Classification Evidence Gate
Cost changes are categorized into behavioral classifications only when substantiated by empirical telemetry:
* **`USAGE`**: Spec is unchanged, usage/volume metrics exist, and usage quantity changed by $> 5\%$.
* **`PRICE_CONFIG`**: Telemetry shows an instance type or storage tier modification (e.g., `m5.large` $\to$ `m5.xlarge`).
* **`NOT_AVAILABLE`**: Default when spec or volume telemetry is missing. Atlas never guesses or assumes usage without evidence.

---

## 5. Spend Concentration Index (HHI)

Atlas evaluates cloud vendor and service concentration using the **Herfindahl-Hirschman Index (HHI)**:
$$HHI = \sum_{i=1}^{N} s_i^2$$
where $s_i$ is the percentage market share of service/account $i$ ($0 \le s_i \le 100$).

* **Range**: $0$ to $10,000$.
* **Interpretation**:
  - $HHI < 1,500$: **Diversified** spend footprint.
  - $1,500 \le HHI \le 2,500$: **Moderate Concentration**.
  - $HHI > 2,500$: **Highly Concentrated** (e.g. EC2/RDS dominating $> 70\%$ of technology budget).

*Architectural Principle*: The Concentration Index is strictly descriptive. It informs risk management without penalizing legitimate architectural focus.

---

## 6. Capacity Headroom & Efficiency Analysis

### 6.1 Observed Utilization Headroom
Headroom represents the measured gap between peak workload demands and provisioned capacity:
$$\text{observed\_utilization\_headroom} = 100\% - p95\text{\_utilization}$$

*Architectural Rule*: Headroom is purely descriptive telemetry. It is **never** conflated with immediately removable capacity or cost savings.

### 6.2 Waste Decoupling
* Headroom does NOT equal waste.
* Addressable waste is strictly derived from Phase 5 evidence-backed waste models (`UNATTACHED_VOLUME`, `IDLE_DATABASE`, `OVERSIZED_INSTANCE`, etc.), not from synthetic formulas like `idle_cost = (100 - util) * cost`.

### 6.3 Unit Economics Telemetry Contract
Atlas specifies contracts for unit economics (Cost per API Request, Cost per Active User, Cost per GB Ingested). In demo mode without external business instrumentation, all unit economics are explicitly reported as `SufficiencyStatus.NOT_CONFIGURED` with `cost_per_unit = null`. Zero phantom metrics are manufactured.

---

## 7. Scenario Modeling Workbench & Simulation Engine

The Scenario Engine (`apps/api/app/analytics/scenarios/`) provides an interactive simulation workbench for testing architectural and financial decisions.

### 7.1 What-If Simulations
Users simulate changes across three primary archetypes:
1. **Rightsizing**: Downscaling compute/database capacity based on verified headroom.
2. **Purchasing Commitments**: Applying 1-year or 3-year Compute Savings Plans or Reserved Instances (modeling $25\%\text{--}40\%$ cost reduction with lock-in tradeoff).
3. **Decommissioning**: Terminating orphan volumes, idle read replicas, or obsolete snapshots.

### 7.2 Architectural Constraint Enforcement
The engine validates modifications against strict production safety constraints:
* **No Production Off-Hours Shutdown**: Rejects off-hours scheduling for production workloads (`ENV=production` or `tier=prod`).
* **Preserve High Availability**: Rejects terminating instances or databases that would drop cluster redundancy below required HA thresholds.
* **Storage Preservation**: Prevents volume deletions where snapshots or disaster recovery compliance is unverified.

---

## 8. Optimization Portfolio Modeling & Conflict Detection

When multiple optimization recommendations exist, aggregating their savings requires dependency and compatibility checking (`apps/api/app/analytics/optimization/`).

### 8.1 Mutual Exclusivity
When an opportunity provides alternative resolution paths (e.g., Option A: Modernize to Graviton vs. Option B: Rightsizing down to t4g.medium), they are tagged as `MUTUALLY_EXCLUSIVE`. The portfolio selects the primary recommendation and excludes conflicting alternates from the `total_compatible_monthly_savings`.

### 8.2 Dependency Classification
Atlas distinguishes:
- `REQUIRED_DEPENDENCY`: A change that must precede or accompany an action (e.g., verifying database snapshot before deletion).
- `RECOMMENDED_PRECAUTION`: A best-practice precaution (e.g., load testing prior to CPU reduction).

### 8.3 Transparent Multi-Dimensional Tradeoffs (No Magic Composite Score)
Atlas explicitly rejects single composite scores (e.g., "Optimization Score: 78/100"). Recommendations are evaluated across 5 independent, transparent dimensions:
1. **Financial Impact** (Monthly INR savings)
2. **Confidence** ($0\%\text{--}100\%$ evidence backing)
3. **Risk Level** (`LOW`, `MEDIUM`, `HIGH`)
4. **Implementation Complexity** (`LOW`, `MEDIUM`, `HIGH`)
5. **Reversibility** (`REVERSIBLE`, `PARTIALLY_REVERSIBLE`, `IRREVERSIBLE`)

---

## 9. Data Sufficiency Framework

Every analytical endpoint and metric returns an explicit `sufficiency_status`:
* **`AVAILABLE`**: Complete telemetry and baseline data exist.
* **`INSUFFICIENT_DATA`**: Less than required sample size (e.g., $< 7$ days of spend).
* **`NOT_CONFIGURED`**: Integration or telemetry pipeline is not connected (e.g. business unit economics).
* **`NOT_APPLICABLE`**: Telemetry is not relevant to this resource type (e.g. CPU headroom on an EBS volume).

---

## 10. Analytical Explanation & Audit Provenance

Every calculation produces a structured, machine-readable `AnalyticalExplanation` object containing:
- `observations`: Raw counts and sample data points analyzed.
- `derived_metrics`: Intermediate statistical outputs.
- `classification`: Determined regime, trend, or category.
- `evidence`: Bulleted human-verifiable evidence claims.
- `method`: Identifier of the exact algorithm used.
- `parameters`: Configured thresholds and rolling window sizes.
- `assumptions`: Declared pricing bases, discount terms, and baseline windows.
- `version`: Engine version tag (`atlas-analytics-v1` or `atlas-scenarios-v1`).

---

## 11. Limitations & Future AWS Integration Boundary

### Current Offline Boundaries
* Analytical calculations execute purely against the relational database and synthetic telemetry.
* No live AWS CloudWatch, Cost Explorer, or Compute Optimizer APIs are invoked.

### Transition to Live AWS Integration (Phase 7+)
When live cloud providers are connected:
1. **Financial Telemetry**: Ingested via AWS Cost and Usage Reports (CUR 2.0) into `CostRecord`.
2. **Operational Telemetry**: Ingested via CloudWatch / AWS Config into `CloudResource.specs_json`.
3. **Engine Portability**: The entire `apps/api/app/analytics/` module requires zero modifications when transitioning to live data, as it consumes standard Pydantic models decoupled from provider transport layers.
