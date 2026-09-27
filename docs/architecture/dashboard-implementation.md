# NEXORA ATLAS — Phase 4: Dashboard & Core Interface Implementation

**Status**: Implemented & Formally Verified  
**Product**: NEXORA ATLAS (Technology Cost Intelligence & Optimization Platform)  
**Date**: September 2026  
**Safety Status**: 100% Offline (AWS Network Disabled, Zero Cloud Mutations)  

---

## 1. Executive Summary & Design Vision

Phase 4 bridges the deterministic synthetic cloud environment (Phase 3) and relational persistence layer (Phase 2) into an enterprise-grade **Technology Cost Intelligence Command Center**.

The interface answers the executive and engineering question:
> **"What is happening with our technology money, and where should I look?"**

Rather than behaving like a passive cloud monitoring dashboard or infrastructure list, Atlas enforces an opinionated FinOps information hierarchy:

$$\text{MONEY} \longrightarrow \text{CHANGE} \longrightarrow \text{PROBLEM} \longrightarrow \text{OPPORTUNITY} \longrightarrow \text{ACTION}$$

```
┌────────────────────────────────────────────────────────────────────────┐
│                        NEXORA ATLAS COMMAND CENTER                     │
├────────────────────────────────────────────────────────────────────────┤
│ [MONEY]       Total 90d Spend: ₹36,83,194.61  | Run-Rate: ₹12,50,000   │
│ [CHANGE]      Run-Rate Change: +14.2%         | Prev 30d: ₹10,94,200   │
│ [PROBLEM]     Active Anomalies: 4 (1 Critical, 2 High, 1 Med)          │
│ [OPPORTUNITY] Potential Savings: ₹4,60,000/mo (₹55,20,000/yr)          │
│ [ACTION]      Concrete Right-Sizing & Orphan EBS Proposals             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Information Architecture & Navigation

The platform provides a cohesive 9-section application shell built with React 19, TypeScript, and Tailwind CSS:

1. **Overview Dashboard** (`/dashboard`): Strategic command center with executive KPI strip, 90-day spend trend SVG chart with operational event markers, service breakdown, account cards, active anomaly preview, optimization opportunities, and immutable audit activity.
2. **Spend Explorer** (`/spend`): Multi-dimensional spend intelligence with 7d/30d/90d period toggles, account and service filters, and paginated resource-level spend attribution.
3. **Anomaly Center** (`/anomalies`): Empirical telemetry fact cards split from algorithmic root-cause hypotheses with severity filtering.
4. **Optimization Center** (`/optimization`): Auditable cloud waste detection, right-sizing candidates, and potential rupee savings grouped by category.
5. **Opportunity Dossier** (`/optimization/:id`): Deep-dive telemetry evidence (CPU, memory, idle duration), spec diff comparison, and concrete recommendation branches.
6. **Scenario Simulator** (`/scenarios`): What-if modeling workbench comparing baseline run-rates against proposed infrastructure modifications.
7. **Cost Forecast** (`/forecast`): Synthetic statistical spend projections with confidence bounds and algorithmic attribution.
8. **Resource Inventory** (`/resources`): Dense searchable asset inventory across compute, database, and storage with 30-day attributed costs.
9. **Cloud Integrations** (`/integrations`): Deterministic AWS ingestion telemetry, read-only IAM verification, and AWS Safety Rule enforcement.
10. **Platform Settings** (`/settings`): Tenant configuration, INR currency standards, Asia/Kolkata timezone, and dual-database architecture.

---

## 3. Backend Services & REST API Specification

All endpoints are mounted under `/api/v1/` and operate via strict multi-tenant resolution (`TenantContext`) backed by SQLAlchemy 2.0 and database-portable SQL queries.

### 3.1 Endpoint Directory

| Method | Path | Service Method | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/dashboard/summary` | `DashboardService.get_summary` | Executive KPI metrics & run-rate delta |
| `GET` | `/api/v1/dashboard/spend-trend` | `DashboardService.get_spend_trend` | Daily spend curve & operational event markers |
| `GET` | `/api/v1/dashboard/service-breakdown`| `DashboardService.get_service_breakdown` | Ranked service spend & percentages |
| `GET` | `/api/v1/dashboard/account-breakdown`| `DashboardService.get_account_breakdown` | Account-level spend distribution |
| `GET` | `/api/v1/dashboard/recent-activity` | `DashboardService.get_recent_activity` | Immutable audit log event feed |
| `GET` | `/api/v1/spend` | `SpendService.get_spend_explorer` | Multidimensional spend explorer with filters |
| `GET` | `/api/v1/anomalies` | `AnomalyService.get_anomalies` | Severity & status filterable anomaly list |
| `GET` | `/api/v1/anomalies/{id}` | `AnomalyService.get_anomaly_detail` | Detailed anomaly facts & hypotheses |
| `GET` | `/api/v1/optimization` | `OptimizationService.get_overview` | Waste categories & total potential savings |
| `GET` | `/api/v1/optimization/{id}` | `OptimizationService.get_opportunity_detail`| Opportunity dossier & recommendation options |
| `GET` | `/api/v1/resources` | `ResourceService.get_resources` | Paginated resource catalog with 30d spend |
| `GET` | `/api/v1/resources/{id}` | `ResourceService.get_resource_detail` | Single resource metadata & tags |
| `GET` | `/api/v1/scenarios` | `ScenarioService.get_scenarios` | What-if simulation models & changes |
| `GET` | `/api/v1/forecast` | `ForecastService.get_forecast` | Synthetic forward projections & bounds |

---

## 4. Mathematical Reconciliation Standard

The backend enforces strict cross-endpoint mathematical reconciliation verified via automated integration tests:

1. **Dashboard Total vs. Spend Explorer Total**:
   $$\text{Dashboard Total Spend (90d)} = \text{Spend Explorer Total Spend (90d)} = ₹36,83,194.61$$
2. **Monthly Run-Rate Reconciliation**:
   $$\text{Dashboard Monthly Run Rate} = \text{Spend Explorer (30d Period Total)} = ₹12,50,000.00$$
3. **Service Breakdown Reconciliation**:
   $$\sum \text{service\_breakdown}[\text{spend}] = \text{Total Period Spend}$$
4. **Account Breakdown Reconciliation**:
   $$\sum \text{account\_breakdown}[\text{spend}] = \text{Total Period Spend}$$
5. **Optimization Run-Rate Reduction**:
   $$\text{Total Monthly Potential Savings} = ₹4,60,000.00 \quad (\text{Annualized: } ₹55,20,000.00)$$

---

## 5. Telemetry Separation: Observed Facts vs. Algorithmic Inference

In accordance with Atlas core principles, the interface never blurs measured data with statistical hypotheses:

* **Observed Facts (Telemetry)**: Concrete billing rows, timestamps, actual measured spend (₹34,200), baseline historical average (₹8,500), and detection trigger rule. Displayed with cold, empirical sky-blue UI cues.
* **Inferred Analysis (Hypothesis)**: Model confidence score (92.5%), inferred root-cause explanation (e.g. "K8s cluster batch ETL loop"), and probable failure modes. Displayed with distinct purple algorithmic tags clearly labeled as `ALGORITHM ESTIMATE`.

---

## 6. Financial Formatting Standard

All monetary metrics are standardized through `apps/web/src/lib/format.ts`:

* **Exact Tabular Currency**: Uses `Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' })` producing correct Indian numbering commas: `₹36,83,194.61`.
* **Compact FinOps Badges**:
  * Values $\ge 1\,\text{Crore}$ ($10^7$): Formatted as `₹2.40Cr`.
  * Values $\ge 1\,\text{Lakh}$ ($10^5$): Formatted as `₹4.60L`, `₹36.83L`.
  * Values $\ge 1\,\text{Thousand}$ ($10^3$): Formatted as `₹14.5K`.
* **Timezone Standard**: Displayed in `Asia/Kolkata` (IST, UTC+05:30).

---

## 7. Responsive Viewport Verification

The interface layout was engineered with fluid CSS grid and flexbox layouts to ensure pristine readability across enterprise screen widths:

* **1440px (Desktop Command Center)**: 4-column KPI strip, full SVG interactive trend chart with event overlay, side-by-side service ranking bar chart and account cards, 2-column anomaly observed/inferred split cards.
* **1280px (Standard Laptop)**: Responsive 3-column layouts with horizontal chart overflow handling and dense tabular presentation.
* **1024px (Compact Workstation / Tablet)**: 2-column KPI cards, stacked breakdown lists, accessible touch targets, and collapsible sidebar.

---

## 8. Automated Verification Suite

The entire implementation has passed rigorous test automation across backend services, REST APIs, database queries, and frontend user interfaces:

```text
======================= 35 passed in 37.99s (Python / pytest) =======================
  ✓ test_dashboard_summary_endpoint
  ✓ test_spend_trend_and_events
  ✓ test_service_and_account_breakdowns
  ✓ test_spend_explorer_reconciliation
  ✓ test_anomalies_observed_vs_inferred
  ✓ test_optimization_overview_and_detail
  ✓ test_resources_inventory_and_search
  ✓ test_scenarios_and_forecast_fixtures
  ✓ test_financial_reconciliation_exact
  ... (26 additional persistence and domain tests)

======================= 21 passed in 15.93s (TypeScript / Vitest) ===================
  ✓ Application Shell & Smoke Tests (Brand, Demo Banner, Navigation, Provider)
  ✓ Command Palette Component (Filtering, Keyboard Nav, Modal Triggers)
  ✓ Dashboard Charts (SpendTrendChart SVG, ServiceBreakdownChart, ObservedVsInferredCard)
  ✓ Financial Formatters (Indian Rupee Lakhs/Crores, Precision, Dates, Percentages)

TOTAL VERIFIED TESTS: 56 / 56 PASSED (100%)
```

---

## 9. AWS Safety Rule Compliance

Throughout Phase 4 development:
1. **0 AWS network connections made**.
2. **0 AWS credentials requested or stored**.
3. **0 boto3 SDK calls executed**.
4. **100% deterministic offline operations** running on local database persistence.
