# NEXORA ATLAS — Master Architectural Specification & Engineering Manual

> **The Technology Financial Intelligence Command Center**  
> *"Know where technology money is going, why it changed, what the evidence says, and what to do about it."*  
> Document Version: `3.0.0` | System Release: `Phase 9 (Milestones 1–4 Verified)` | Test Baseline: `277 Backend / 62 Frontend (100% Green)`  
> Target Audience: Enterprise FinOps Architects, Principal Engineers, Security Officers, Infrastructure Leads

---

## Master Table of Contents

1. [System Architecture](#1-system-architecture)
   - 1.1 Architectural Doctrine & Foundational Principles
   - 1.2 Modular Monolith vs Microservices Rationale
   - 1.3 End-to-End Information & Verification Pipeline
   - 1.4 System Trust Boundaries & Safety Guarantees
   - 1.5 Multi-Tenant Scoping & Authoritative Isolation
   - 1.6 Epistemic Classification Hierarchy
2. [System Design](#2-system-design)
   - 2.1 Canonical Relational Domain Data Model
   - 2.2 Dual-Dialect Storage Strategy (PostgreSQL 16 & SQLite 3)
   - 2.3 Database Schema & Alembic Migration Lineage
   - 2.4 API Transport & Routing Tier (FastAPI & Pydantic v2)
   - 2.5 Data Access Layer (Repository Pattern)
   - 2.6 Application Orchestration Services
   - 2.7 AI Explanation Subsystem Design (Phase 9 M1–M4)
3. [UI/UX Guide & Master Specification](#3-uiux-guide--master-specification)
   - 3.1 Design Philosophy & Visual Tone
   - 3.2 Design Tokens & Surface Hierarchy
   - 3.3 The 7-Step Analytical UX Grammar
   - 3.4 Command Center & Global Chrome
   - 3.5 Signature Visual Subsystems
   - 3.6 Complete Page-by-Page Breakdown
   - 3.7 Accessibility & Monospace Financial Typography
4. [Technologies Used and Architectural Rationale](#4-technologies-used-and-architectural-rationale)
   - 4.1 Backend & Persistence Stack
   - 4.2 Frontend & Presentation Stack
   - 4.3 Validation, AI & Testing Infrastructure
   - 4.4 Financial Precision Doctrine (`Decimal` vs IEEE 754 Floating-Point)
5. [Exhaustive File & Folder Inventory](#5-exhaustive-file--folder-inventory)
   - 5.1 Root Configuration & Operational Tooling
   - 5.2 Documentation & ADRs (`docs/`)
   - 5.3 Shared Packages (`packages/`)
   - 5.4 Backend Codebase Breakdown (`apps/api/`)
   - 5.5 Frontend Codebase Breakdown (`apps/web/`)
6. [Future Plans & Roadmap](#6-future-plans--roadmap)
   - 6.1 Phase 9 Completion: Milestones 5 through 8
   - 6.2 Phase 10: Controlled Execution & IaC Pull Request Automation
   - 6.3 Phase 11: Multi-Cloud Unified Mesh (GCP, Azure, Kubernetes)
   - 6.4 Phase 12: Provable Autonomous FinOps Agents
7. [Known Problems, Limitations & Edge Cases](#7-known-problems-limitations--edge-cases)
   - 7.1 Cloud Provider Ingestion Latency (AWS CE 24–48h Lag)
   - 7.2 Telemetry API Rate Limits & Throttling
   - 7.3 Zero-Telemetry Serverless Workloads
   - 7.4 SQLite Concurrency & Locking
   - 7.5 Windows Python 3.13 Alembic Path Separator Deprecation
   - 7.6 Fixed-Point Decimal Transport Serialization
8. [Mathematical Formulations & Formal Proofs](#8-mathematical-formulations--formal-proofs)
   - 8.1 Spend Aggregation & Period Deltas
   - 8.2 Dual Driver Contribution Metrics (Absolute vs Net)
   - 8.3 Rolling Baselines & Statistical Z-Score Anomalies
   - 8.4 Volatility Index & Deterministic Trend Precedence
   - 8.5 Behavioral Spend Regime State Machine
   - 8.6 Herfindahl-Hirschman Concentration Index (HHI)
   - 8.7 Local Nearest Rank Telemetry Percentiles ($p95$)
   - 8.8 Telemetry Sampling Coverage & Trustworthiness Scoring
   - 8.9 Numerical Claim Verification Gate ($\pm 1.0\%$ Relative Error)
   - 8.10 Annualized Financial Savings Invariant
   - 8.11 Cryptographic Context Hashing
9. [Comprehensive Operator & Developer Manual](#9-comprehensive-operator--developer-manual)
   - 9.1 Local Development Environment Setup
   - 9.2 Running with Docker Compose (PostgreSQL Production)
   - 9.3 Database Migrations & Seeding Synthetic Data
   - 9.4 Executing Verification Test Suites
   - 9.5 Environment Variable Reference
   - 9.6 Debugging Validation Rejections & AI Auditing

---

# 1. System Architecture

## 1.1 Architectural Doctrine & Foundational Principles

NEXORA ATLAS is an enterprise-grade cloud cost intelligence, optimization modeling, and natural-language explanation platform. It is designed to overcome the three structural failures of conventional cloud cost management tools:
1. **Opaque Aggregations**: Traditional tools present high-level billing graphs without actionable root-cause attribution, masking structural cost shifts behind gross numbers.
2. **Untrusted Heuristics & Black-Box AI**: "Auto-pilot" optimization bots emit phantom recommendations, hallucinate savings percentages, or execute unreviewed destructive modifications.
3. **Telemetry Conflation**: Financial invoicing records are conflated with real-time operational telemetry, leading to erroneous rightsizing suggestions on bursty or memory-bound workloads.

To eliminate these vulnerabilities, NEXORA ATLAS operates under a strict, non-negotiable architectural doctrine:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      CORE ARCHITECTURAL DOCTRINE                       │
│                                                                        │
│   1. EVIDENCE FIRST, DETERMINISTIC CORE, ZERO UNCHECKED PROJECTIONS    │
│   2. ABSOLUTE READ-ONLY BOUNDARY (ZERO MUTATING INFRASTRUCTURE CALLS)  │
│   3. COMPLETE DECOUPLING OF FINANCIAL BILLING FROM TELEMETRY           │
│   4. FIVE-TIER EPISTEMIC CLASSIFICATION ON EVERY CLAIM                 │
│   5. AUDITABLE PROVENANCE & STRICT CANONICAL DATA NORMALIZATION        │
│   6. STRICT FINANCIAL PRECISION (DECIMAL ARITHMETIC, ZERO FLOATS)      │
│   7. ZERO AI-CONFIDENCE PROHIBITION (EPISTEMIC GROUNDING ONLY)         │
└────────────────────────────────────────────────────────────────────────┘
```

## 1.2 Modular Monolith vs Microservices Rationale

NEXORA ATLAS is deliberately constructed as a **Modular Monolith**. 

### Strategic Rationale
* **Zero Distributed Latency**: In FinOps, cost driver attribution and rolling baseline calculations require evaluating millions of billing records across 90-day windows. Microservice RPC boundaries introduce network serialization overhead, connection pool exhaustion, and eventual consistency lag.
* **Transactional Integrity**: Financial operations require atomic ACID guarantees across accounts, resources, spend records, and anomaly records.
* **Deterministic Testability**: A modular monolith enables running the entire 277-test backend suite and 62-test frontend suite in under 70 seconds locally with zero external network or cloud mock dependencies.
* **Clean In-Process Boundaries**: Strict boundary enforcement is achieved through Python typing, repository encapsulation, and clear domain separation (`apps/api/app/intelligence`, `app/analytics`, `app/integrations`, `app/ai`) rather than physical network boundaries.

```mermaid
flowchart TD
    subgraph Client ["Client Presentation Tier (apps/web)"]
        UI["React 19 SPA (Vite + Tailwind)"]
        State["Client State & Typed API SDK"]
        UI --> State
    end

    subgraph API ["Transport & Auth Tier (apps/api/app/api)"]
        Gateway["FastAPI Gateway (/api/v1/*)"]
        AuthMiddleware["Tenant Context & Security Middleware"]
        Gateway --> AuthMiddleware
    end

    subgraph Services ["Application Orchestration Tier (apps/api/app/services)"]
        SpendSvc["Spend Service"]
        IntelSvc["Intelligence Service"]
        AnalyticsSvc["Analytics Service"]
        IntegrationSvc["Integrations Service"]
        AISvc["AI Orchestration Engine"]
    end

    subgraph Engines ["Pure Domain Logic Tier (apps/api/app/engines, analytics, ai)"]
        BaselineEng["Baseline Engine"]
        AnomalyEng["Anomaly Engine"]
        WasteEng["Waste Engine"]
        DriverEng["Driver Attribution Engine"]
        ScenarioEng["Scenario Simulation Engine"]
        ValidatorEng["Numerical Claim Validator"]
    end

    subgraph Integration ["Provider Ingestion Tier (apps/api/app/integrations)"]
        ClientFactory["AWS Client Factory (AssumeRole)"]
        CostExplorer["Cost Explorer Adapter (Dual-Path)"]
        ResourceScanner["Resource Metadata Scanner"]
        CWAdapter["CloudWatch Telemetry Adapter"]
        SafetyAST["Read-Only AST Safety Guard"]
    end

    subgraph Persistence ["Data Access & Storage Tier (apps/api/app/repositories, models)"]
        Repos["Repository Pattern (Generic CRUD + Scoped)"]
        ORM["SQLAlchemy 2.0 Async Models"]
        DB[(PostgreSQL 16 / SQLite Fallback)]
    end

    State -- HTTPS/JSON --> Gateway
    AuthMiddleware --> SpendSvc & IntelSvc & AnalyticsSvc & IntegrationSvc & AISvc
    SpendSvc & IntelSvc & AnalyticsSvc & ScenarioEng --> Repos
    IntelSvc --> BaselineEng & AnomalyEng & WasteEng
    AnalyticsSvc --> DriverEng & ScenarioEng
    AISvc --> ValidatorEng
    IntegrationSvc --> ClientFactory
    ClientFactory --> SafetyAST
    SafetyAST --> CostExplorer & ResourceScanner & CWAdapter
    Repos --> ORM
    ORM --> DB
```

## 1.3 End-to-End Information & Verification Pipeline

Atlas strictly separates observation, analysis, explanation, and validation into sequential, unidirectional stages:

```text
AWS APIs / Demo Data Engine
            │
            ▼
Canonical Normalization Tier (PostgreSQL / SQLite)
            │
            ▼
Phase 5: Deterministic Intelligence (Baselines, Anomalies, Waste Rules)
            │
            ▼
Phase 6: Advanced Analytics (Drivers, Volatility, Regimes, Scenarios)
            │
            ▼
Phase 8: Operational Telemetry (CloudWatch p95, Coverage Ratios)
            │
            ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      PHASE 9: AI EXPLANATION LAYER                     │
│                                                                        │
│   User Question: "Why did EC2 spend spike in May?"                     │
│         │                                                              │
│         ▼                                                              │
│   1. Scope Authorization: Effective = Requested ∩ Authorized           │
│         │                                                              │
│         ▼                                                              │
│   2. Question Classification & Domain Intent Detection                 │
│         │                                                              │
│         ▼                                                              │
│   3. Deterministic Evidence Retrieval (Database Queries Only)          │
│         │                                                              │
│         ▼                                                              │
│   4. Context Budgeting, Pruning & Injection Sanitization               │
│         │                                                              │
│         ▼                                                              │
│   5. Canonical SHA-256 Hashing (Cryptographic Provenance)              │
│         │                                                              │
│         ▼                                                              │
│   6. AI Provider (Mock / OpenAI) → AICandidateAnswer (UNTRUSTED)       │
│         │                                                              │
│         ▼                                                              │
│   7. 8-Gate Response Validation Engine                                 │
│      ├── Gate 1: Structure & Schema Completeness                       │
│      ├── Gate 2: Epistemic Ceiling & Prohibited Vocabulary             │
│      ├── Gate 3: Zero AI-Confidence Invariant Check                    │
│      ├── Gate 4: Evidence Citation ID Existence                        │
│      ├── Gate 5: Epistemic Alignment Verification                      │
│      ├── Gate 6: Numerical Claim Value Reconciliation (±1.0% Gate)     │
│      ├── Gate 7: Currency & Attribution Grounding                      │
│      └── Gate 8: Audit Logging & Provenance Recording                  │
│         │                                                              │
│         ├── [Passes All Gates] ──────────────────────┐                 │
│         │                                            │                 │
│         └── [Gate Fails & Attempts < 1]              ▼                 │
│                 │                             AIAnswer (VERIFIED)      │
│                 ▼                                    │                 │
│         Controlled One-Shot                          │                 │
│         Targeted Regeneration                        ▼                 │
│                 │                             FinOps Executive         │
│                 └────────────────────────────────────┘                 │
└────────────────────────────────────────────────────────────────────────┘
```

## 1.4 System Trust Boundaries & Safety Guarantees

NEXORA ATLAS establishes four absolute architectural trust boundaries:

### 1. The Absolute Read-Only Boundary
* Atlas **never modifies, deletes, halts, rightsizes, or provisions** cloud infrastructure.
* Integration adapters expose only queries (`get_*`, `list_*`, `describe_*`).
* **AST Static Safety Scanner**: Python's `ast` module parses every file in `apps/api/app/integrations/` during the test suite run (`test_aws_safety.py`). It fails the build if any forbidden SDK token appears (`terminate_instances`, `delete_volume`, `stop_instances`, `create_tags`, `modify_db_instance`, `purchase_reserved_instances_offering`, etc.).

### 2. Telemetry Separation Boundary
* Financial cost records (`CostRecord`) and operational hardware telemetry (`ResourceMetricObservation`) are maintained in separate relational models.
* Financial data represents billed currency from Cost Explorer or CUR.
* Telemetry represents empirical hardware utilization from CloudWatch (CPU, Memory, Network, Disk).
* Optimization rules correlate both dimensions before proposing recommendations, preventing downscaling of memory-bound or bursty instances.

### 3. Untrusted Candidate Boundary
* The AI Provider (e.g. OpenAI GPT-4o or Mock) produces `AICandidateAnswer`, which is treated as **untrusted user input**.
* No candidate answer can reach the user or client interface without passing the 8-Gate Response Validator.
* The AI is completely forbidden from querying databases, executing code, or inspecting unprovided records.

### 4. Tenant Isolation Boundary
* Multi-tenancy is enforced at the repository and service layers.
* Authoritative scope resolution computes:
  $$\text{Effective Scope} = \text{Requested Scope} \cap \text{Authorized Tenant Scope}$$
* Queries containing foreign account IDs or unauthorized resources immediately fail with HTTP 404 or empty sets, preventing cross-tenant information leakage.

## 1.5 Multi-Tenant Scoping & Authoritative Isolation

Every query in the platform is tenant-scoped:
* Core tables carry `organization_id` (or `account_id` foreign-keyed to an account owned by an organization).
* API routes resolve tenant context via `get_current_tenant` dependency.
* Repository base classes mandate filtering by `organization_id`.
* The AI Retrieval subsystem explicitly filters evidence packages by tenant before prompt construction.

## 1.6 Epistemic Classification Hierarchy

Atlas stamps every claim, metric, and recommendation with an **Epistemic Class**:

$$\text{OBSERVED} \succ \text{DERIVED} \succ \text{INFERRED} \succ \text{ASSUMED} \succ \text{PROJECTED} \succ \text{NOT\_AVAILABLE}$$

| Epistemic Class | Definition | Verification Standard |
| :--- | :--- | :--- |
| **`OBSERVED`** | Directly measured empirical fact from an authoritative external system (AWS API, CloudWatch metric). | Cryptographically verifiable or recorded in raw API sync payload with timestamp. |
| **`DERIVED`** | Calculated through a deterministic mathematical formula using only observed inputs (delta, rolling mean, p95). | 100% reproducible by any independent auditor executing the exact formula. |
| **`INFERRED`** | High-probability conclusion deduced from structural patterns or multi-metric correlation. | Supported by explicit heuristics; flags uncertainty if data is missing. |
| **`ASSUMED`** | Declared business baseline, default rate, or unmeasured parameter (e.g. off-peak schedule assumption). | Marked with explicit caveat; never presented as empirical fact. |
| **`PROJECTED`** | Forward-looking estimate or simulation (e.g. 30-day forecast, rightsizing scenario savings). | Explicitly marked with confidence intervals, simulation parameters, and bounds. |
| **`NOT_AVAILABLE`** | Requested data is missing, unmeasured, or outside the collection window. | Explicitly declared; prevents phantom extrapolations. |

---

# 2. System Design

## 2.1 Canonical Relational Domain Data Model

Atlas defines a canonical relational schema isolating domain logic from cloud provider formats:

```mermaid
erDiagram
    ORGANIZATION ||--o{ CLOUD_ACCOUNT : owns
    ORGANIZATION ||--o{ SCENARIO : defines
    ORGANIZATION ||--o{ AI_INTERACTION : audits
    CLOUD_ACCOUNT ||--o{ CLOUD_REGION : spans
    CLOUD_ACCOUNT ||--o{ CLOUD_RESOURCE : provisions
    CLOUD_ACCOUNT ||--o{ COST_RECORD : incurs
    CLOUD_RESOURCE ||--o{ COST_RECORD : attributes
    CLOUD_RESOURCE ||--o{ RESOURCE_METRIC_OBSERVATION : records
    CLOUD_RESOURCE ||--o{ ANOMALY_RECORD : triggers
    CLOUD_RESOURCE ||--o{ OPTIMIZATION_OPPORTUNITY : targets
    OPTIMIZATION_OPPORTUNITY ||--o{ RECOMMENDATION : produces
    INTEGRATION ||--o{ SYNC_JOB : executes

    ORGANIZATION {
        uuid id PK
        string name
        string slug
        string currency
    }

    CLOUD_ACCOUNT {
        uuid id PK
        uuid organization_id FK
        string provider
        string account_id
        string name
        string environment
    }

    CLOUD_RESOURCE {
        uuid id PK
        uuid account_id FK
        string resource_id
        string service_name
        string resource_type
        string region
        json specs_json
    }

    COST_RECORD {
        uuid id PK
        uuid account_id FK
        uuid resource_id FK
        date usage_date
        decimal unblended_cost
        decimal amortized_cost
        decimal usage_quantity
        string usage_unit
        string cost_attribution_level
    }

    RESOURCE_METRIC_OBSERVATION {
        uuid id PK
        uuid resource_id FK
        string metric_name
        datetime start_time
        datetime end_time
        float average
        float maximum
        float p95
        int sample_count
    }

    ANOMALY_RECORD {
        uuid id PK
        uuid account_id FK
        uuid resource_id FK
        date detected_date
        decimal actual_cost
        decimal expected_cost
        float severity_score
        string classification
    }

    OPTIMIZATION_OPPORTUNITY {
        uuid id PK
        uuid resource_id FK
        string opportunity_type
        decimal estimated_monthly_savings
        string risk_level
        string implementation_effort
    }

    AI_INTERACTION {
        uuid id PK
        uuid organization_id FK
        string query_intent
        string context_hash
        json evidence_package_json
        string raw_response
        string verification_status
    }
```

## 2.2 Dual-Dialect Storage Strategy (PostgreSQL 16 & SQLite 3)

The database subsystem (`apps/api/app/core/database.py`) provides seamless dual-dialect compatibility:
* **Production Dialect (PostgreSQL 16)**: Uses `asyncpg` for native UUID types, `JSONB` binary columns, transactional row-locking (`SELECT FOR UPDATE`), and async connection pooling.
* **Development / Test Dialect (SQLite 3)**: Uses `aiosqlite` with dialect abstraction helper functions (`get_json_column()`, `get_uuid_type()`). Automatically enables foreign keys via `PRAGMA foreign_keys = ON;`.

## 2.3 Database Schema & Alembic Migration Lineage

Schema versioning is managed via Alembic:
1. `4b0cbd317c07_initial_schema.py`: Core organizational, accounting, resource, cost, anomaly, optimization, forecast, scenario, and audit logging tables.
2. `6c2e3f8d9b1a_add_resource_metric_observations.py`: Real-time operational telemetry observation storage (`resource_metric_observations`) with multi-column indexing on `(resource_id, metric_name, start_time)`.
3. `7d3e4f1a2b3c_add_ai_interactions.py`: Auditable AI interaction logging, context hashing, and epistemic verification traces (`ai_interactions`).

## 2.4 API Transport & Routing Tier (FastAPI & Pydantic v2)

* Built with **FastAPI** (`apps/api/app/api/v1/router.py`), delivering asynchronous request processing with automatic OpenAPI 3.1 documentation.
* **Pydantic v2** handles validation and serialization. Financial values are validated with custom validators to ensure precision.
* **Standardized JSON Response Envelopes**: Consistent payloads across `/spend`, `/anomalies`, `/optimization`, `/analytics`, `/resources`, and `/ai`.

## 2.5 Data Access Layer (Repository Pattern)

Located in `apps/api/app/repositories/`:
* `BaseRepository[T]`: Implements async generic CRUD operations (`get`, `list`, `create`, `update`, `delete`) with mandatory tenant scoping.
* Specialized Repositories:
  - `CostRepository`: High-performance time-series aggregation, grouping by dimension, delta calculations.
  - `ResourceRepository`: Multi-attribute inventory queries, dynamic JSON specification filtering.
  - `AnomalyRepository`: Statistical anomaly query and resolution tracking.
  - `OptimizationRepository`: Waste findings, recommendation lookup, mutual exclusivity checking.
  - `TelemetryRepository`: Metric observation queries and sampling coverage evaluation.

## 2.6 Application Orchestration Services

Located in `apps/api/app/services/`:
* `SpendService`: Orchestrates spend queries, daily time-series, and dimension breakdowns.
* `IntelligenceService`: Executes Phase 5 rolling baselines and waste detection rules.
* `AnalyticsService`: Orchestrates Phase 6 driver attribution, volatility metrics, regimes, and HHI concentration.
* `TelemetryService`: Ingests CloudWatch telemetry, evaluates sampling sufficiency, and calculates data quality scores.
* `ScenarioService`: Simulates what-if architectural modifications against baseline costs.
* `IntegrationsService`: Manages cloud accounts, STS AssumeRole handshakes, and background sync jobs.

## 2.7 AI Explanation Subsystem Design (Phase 9 M1–M4)

The AI subsystem (`apps/api/app/ai/`) provides grounded natural language intelligence:
* **M1 (Contracts & Types)**: Canonical data models (`app/ai/types.py`, `app/ai/models.py`, `app/ai/contracts.py`). Mandates `Decimal` for financial quantities. Strict zero AI-confidence prohibition.
* **M2 (Retrieval & Context)**: Deterministic evidence retrieval (`app/ai/retrieval/`) spanning 7 domain types. Scope resolution ($\text{Effective} = \text{Requested} \cap \text{Authorized}$). Token budgeting with priority retention. Canonical SHA-256 context hashing.
* **M3 (Provider Layer & Prompting)**: `MockAIProvider` (deterministic offline golden scenarios A–J) and `OpenAIProvider` (production structured output). Strict prompt builder (`app/ai/prompts/builder.py`) enforcing 12 epistemic prompt rules and prompt-injection defense.
* **M4 (Validation & Hallucination Gate)**: 8-gate response validator (`app/ai/validation/gate.py`). Verifies structure, epistemic ceiling, zero AI-confidence, citation ID existence, numeric claims ($\pm 1.0\%$ tolerance gate), and currency grounding. Controlled one-shot regeneration.

---

# 3. UI/UX Guide & Master Specification

## 3.1 Design Philosophy & Visual Tone

NEXORA ATLAS rejects generic "dashboard widgets" in favor of **The Technology Financial Intelligence Command Center**:
* **Visual Tone**: Bloomberg Terminal × Palantir Foundry × Linear × Modern Infrastructure Control Systems.
* **Temperament**: Quietly powerful, sober, surgically precise, high-density.
* **Anti-Pattern**: No noisy decorative gradients, no neon "cyberpunk" glowing cards, no unverified synthetic scores. Every visual element maps to authoritative data or epistemic status.

## 3.2 Design Tokens & Surface Hierarchy

```css
/* Surface Hierarchy */
--atlas-canvas:       #080B10; /* Deepest black-slate base */
--atlas-surface:      #0F141C; /* Primary container surface */
--atlas-elevated:     #141B27; /* Raised card & interactive surfaces */
--atlas-overlay:      #1A2234; /* Floating modals, drawers, tooltips */
--atlas-border:       #1E2638; /* Primary structural dividers */
--atlas-border-soft:  #17202D; /* Subtle secondary dividers */

/* Text & Contrast Scale */
--atlas-text-primary:   #F1F5F9; /* High-contrast headers & active values */
--atlas-text-secondary: #94A3B8; /* Descriptive labels & table headers */
--atlas-text-muted:     #64748B; /* Metadata, timestamps, units */
--atlas-text-disabled:  #475569; /* Inactive elements */

/* Semantic Accents */
--atlas-positive:     #10B981; /* Cost reductions, healthy state, verified claims */
--atlas-warning:      #F59E0B; /* Anomalies, elevated regimes, moderate risk */
--atlas-critical:     #EF4444; /* Cost spikes, runaway spend, high risk */
--atlas-info:         #38BDF8; /* General discovery, links, active filters */
--atlas-primary:      #0EA5E9; /* Brand cyan-blue primary interaction accent */
```

## 3.3 The 7-Step Analytical UX Grammar

Every analytical surface in Atlas strictly follows this continuous chain of reasoning:

$$\text{MONEY} \longrightarrow \text{CHANGE} \longrightarrow \text{CAUSE} \longrightarrow \text{EVIDENCE} \longrightarrow \text{OPPORTUNITY} \longrightarrow \text{SCENARIO} \longrightarrow \text{DECISION}$$

## 3.4 Command Center & Global Chrome

* **`NavigationSpine.tsx`**: Left navigation sidebar featuring brand mark, environment indicators, route links, and data freshness indicators.
* **`GlobalHeader.tsx`**: Top header bar containing breadcrumbs, environment switcher, tenant selector, data freshness badge, and global search activator.
* **`CommandPalette.tsx` (`Ctrl + K` / `Cmd + K`)**: Global modal enabling instantaneous keyboard navigation across pages, resources, anomalies, and quick actions.
* **`DemoBanner.tsx`**: Persistent top banner alerting users when synthetic demo data is active.
* **`AtlasPulse.tsx`**: Real-time heartbeat indicator confirming active backend telemetry connectivity and sync health.

## 3.5 Signature Visual Subsystems

* **`CostTopology.tsx`**: Canonical 5-level deterministic hierarchical graph mapping spend across Organization $\to$ Environment $\to$ Account $\to$ Service $\to$ Resource.
* **`InvestigationTrace.tsx`**: 5-stage causal spine detailing the progression from spend spike detection to root-cause attribution and remediation.
* **`DecisionRoom.tsx`**: Optimization decision room featuring candidate trade-off sliders (savings vs risk vs effort) and implementation playbooks.
* **`FutureStateTopology.tsx`**: Visual comparison between current observed topology and simulated post-optimization future state.
* **`EpistemicBadge.tsx`**: Color-coded pill indicating the epistemic tier of any metric or statement.
* **`ObservedVsInferredCard.tsx`**: High-contrast card clearly delineating empirical observations from forward-looking projections.

## 3.6 Complete Page-by-Page Breakdown

1. **Command Center (`/dashboard`)**: Executive view with Month-to-Date spend, spend velocity, active anomalies, top optimization candidates, and 30-day forecast trajectories.
2. **Spend Explorer (`/spend`)**: Interactive spend analysis supporting dynamic grouping (Service, Account, Region), date filtering, driver attribution, and regime breakdowns.
3. **Changes & Anomalies (`/changes`, alias `/anomalies`)**: Statistical spend anomalies, Z-score severity ratings, root-cause attribution, and status tracking.
4. **Optimization Workspace (`/optimization`)**: Portfolio view of addressable waste, rightsizing candidates, and commitment modeling.
5. **Recommendation Detail (`/optimization/:id`)**: Engineering case file with architectural rationale, risk assessment, CLI execution commands, and rollback procedures.
6. **Resource Inventory & Intelligence (`/resources`, `/resources/:id`)**: Searchable cloud catalog with technical specifications, historical cost curves, and CloudWatch telemetry sparklines.
7. **Scenarios Simulation Workbench (`/scenarios`)**: Interactive sandbox simulating rightsizing, schedule changes, and commitment purchases with invariant checks.
8. **Spend Forecast (`/forecast`)**: Forward-looking spend trajectories across 30, 60, and 90 days with historical baseline overlays and confidence bands.
9. **Integrations Control Room (`/integrations`)**: Cloud provider management interface displaying AWS AssumeRole connection status, permission probe matrices, and sync triggers.
10. **Ask Atlas Drawer & Console**: Conversational intelligence panel delivering verified answers, interactive evidence citation pills, and epistemic reliability badges.

## 3.7 Accessibility & Monospace Financial Typography

* **Monospace Tabular Numerals (`font-mono`)**: All monetary figures, percentages, and metrics use monospace font styles to prevent layout jitter and align decimal points in tables.
* **High-Contrast Dark Theme**: All text meets WCAG AA contrast standards ($\ge 4.5:1$ against surface backgrounds).
* **Keyboard First**: Full keyboard navigability via `Tab`, arrow keys, `Escape`, and `Ctrl + K`.

---

# 4. Technologies Used and Architectural Rationale

| Technology | Layer / Area | Version | Architectural Rationale & Why It Was Selected |
| :--- | :--- | :--- | :--- |
| **FastAPI** | Backend Web Framework | `>=0.110.0` | Native asynchronous request handling (`asyncio`), high-speed serialization with Pydantic v2, automatic OpenAPI schema generation, and clean dependency injection. |
| **SQLAlchemy** | Persistence ORM | `2.0+ (asyncio)` | Modern type-annotated Declarative ORM. Pure async engine support (`AsyncSession`). Eliminates N+1 queries through explicit `joinedload` and `selectinload`. |
| **Pydantic** | Validation & Serialization | `v2.6+` | Rust-backed validation core (`pydantic-core`). Extremely fast, strict contract enforcement, and native support for custom data types (`Decimal`). |
| **PostgreSQL** | Production Database | `16.x` | Enterprise relational database with native UUID types, `JSONB` query optimization, row-level locking (`FOR UPDATE`), and ACID guarantees. |
| **SQLite (aiosqlite)** | Dev / CI Database | `3.x` | Zero-Docker embedded fallback allowing developers to run the entire backend and test suite offline without external infrastructure. |
| **Alembic** | Database Migrations | `>=1.13.0` | Version-controlled, declarative database schema migrations supporting both PostgreSQL and SQLite dialects. |
| **Boto3** | Cloud SDK | `>=1.34.0` | Official AWS SDK wrapped in custom read-only adapter layers with AST-enforced safety guardrails. |
| **OpenAI SDK / httpx** | AI Integration | `>=1.14.0` | Asynchronous client abstraction isolating external LLM calls behind deterministic evidence retrieval and post-generation validation gates. |
| **Pytest / Pytest-Asyncio** | Backend Testing | `8.x` | Deterministic async test runner covering all 277 backend unit, integration, property, and world tests with zero flaky network dependencies. |
| **React** | Frontend UI Framework | `19.x` | Modern reactive UI framework utilizing concurrent rendering, state ergonomics, and high component composability. |
| **TypeScript** | Frontend Language | `5.3+` | Strict static typing across all UI state, API client contracts, and domain models, preventing runtime undefined errors. |
| **Vite** | Build Tool & Dev Server | `5.x` | High-performance Rollup-based bundler and dev server providing instantaneous Hot Module Replacement (HMR) and optimized chunk splitting. |
| **Tailwind CSS** | Styling System | `3.4+` | Utility-first CSS framework configured with a bespoke FinOps design system (slate/dark palette `#080B10`, monospace financial tabular numbers). |
| **Lucide React** | Icon System | `0.348+` | Clean, lightweight SVG icon package providing consistent visual affordances across infrastructure resources and status indicators. |
| **Vitest** | Frontend Testing | `1.x` | Blazing-fast Vite-native test runner executing all 62 frontend component and integration tests with jsdom. |

## 4.4 Financial Precision Doctrine (`Decimal` vs IEEE 754 Floating-Point)

In cloud financial management, binary floating-point representation errors (IEEE 754) can cause severe cumulative rounding drift (e.g. `0.1 + 0.2 = 0.30000000000000004`). 
* NEXORA ATLAS strictly mandates `from decimal import Decimal` for all currency amounts, unblended/amortized costs, and savings calculations.
* Database columns use `Numeric(18, 4)`.
* Pydantic schemas enforce `Decimal` for all numeric claims and financial figures.
* Floating-point `float` is strictly limited to non-financial statistical metrics (e.g. CPU utilization %, sample standard deviation, severity scores).

---

# 5. Exhaustive File & Folder Inventory

Below is the complete architectural inventory of every file and directory across the repository.

```
d:\Nexora Atlas\
├── README.md
├── package.json
├── Makefile
├── SYSTEM_DOCUMENTATION.md
├── UI_UX_MASTER_SPECIFICATION.md
├── run-all.bat / run-all.ps1
├── run-api.bat / run-web.bat / seed.bat
├── docs/
├── infra/
├── scripts/
├── packages/
│   ├── design-system/
│   └── shared-types/
├── apps/
│   ├── api/
│   └── web/
```

## 5.1 Root Configuration & Operational Tooling

* **`README.md`**: Project overview, architecture summary, local development instructions, and test commands.
* **`package.json`**: Root workspace definition orchestrating shared tasks across `apps/` and `packages/`.
* **`Makefile`**: Standardized workflow targets (`make test`, `make seed`, `make run-api`, `make run-web`, `make lint`).
* **`SYSTEM_DOCUMENTATION.md`**: This master technical specification and engineering manual.
* **`UI_UX_MASTER_SPECIFICATION.md`**: Master design system and visual UX specification.
* **`run-all.bat` / `run-all.ps1`**: Cross-platform one-click scripts to launch both API and Web dev servers.
* **`run-api.bat` / `run-web.bat` / `seed.bat`**: Individual helper scripts for launching services and seeding demo data.

## 5.2 Documentation & ADRs (`docs/`)

* **`docs/architecture/system.md`**: High-level modular monolith architecture document detailing layer responsibilities.
* **`docs/architecture/data-model.md`**: Data dictionary specifying column definitions, foreign keys, and indexing.
* **`docs/architecture/database-implementation.md`**: Dual-database strategy (PostgreSQL vs SQLite fallback) and async session lifecycle.
* **`docs/architecture/demo-data-engine.md`**: Specifications for synthetic generation algorithms, account topologies, and anomaly scenarios.
* **`docs/architecture/dashboard-implementation.md`**: Interface layout specifications, KPI rollup contracts, and client caching rules.
* **`docs/architecture/intelligence-engine.md`**: Algorithmic rules for Phase 5 rolling baselines, Z-score anomalies, and waste detection heuristics.
* **`docs/architecture/advanced-analytics.md`**: Mathematical formulation of Phase 6 driver attribution, volatility metrics, HHI concentration, and portfolio optimization models.
* **`docs/architecture/aws-integration.md`**: Security specifications for cross-account STS AssumeRole, dual-path Cost Explorer queries, and read-only AST safety scanning.
* **`docs/architecture/telemetry-separation.md`**: Foundational design document establishing the strict decoupling between financial billing records and operational hardware telemetry.
* **`docs/decisions/001-modular-monolith.md`**: ADR-001 recording the justification for a modular monolith over microservices.
* **`docs/decisions/002-dual-database-strategy.md`**: ADR-002 recording the justification for supporting both PostgreSQL and SQLite fallback.
* **`docs/product/mvp.md`**: Product requirement baseline for the minimum viable cost intelligence platform.
* **`docs/product/optimization-engine.md`**: Product requirements for rule-based rightsizing, idle resource detection, and commitment modeling.
* **`docs/product/scenario-engine.md`**: Functional specifications for interactive "What-If" architectural simulation workbenches.

## 5.3 Shared Packages (`packages/`)

* **`packages/shared-types/index.ts`**: Shared TypeScript interface definitions mirroring backend canonical schemas for cross-package consistency.
* **`packages/design-system/index.ts`**: FinOps design tokens, shared color palettes, typography rules, and threshold constants used across web components.

## 5.4 Backend Codebase Breakdown (`apps/api/`)

### 5.4.1 Database Migrations (`apps/api/alembic/`)
* **`alembic/env.py`**: Migration harness configuring SQLAlchemy metadata and multi-dialect execution.
* **`alembic/script.py.mako`**: Migration file generation template.
* **`alembic/versions/4b0cbd317c07_initial_schema.py`**: Initial schema migration creating core organizational, billing, resource, anomaly, optimization, forecast, and scenario tables.
* **`alembic/versions/6c2e3f8d9b1a_add_resource_metric_observations.py`**: Phase 8 migration adding `resource_metric_observations` with compound indexing.
* **`alembic/versions/7d3e4f1a2b3c_add_ai_interactions.py`**: Phase 9 migration adding `ai_interactions` for audit logging, context hashing, and claim verification.

### 5.4.2 Core Infrastructure (`apps/api/app/core/`)
* **`app/core/config.py`**: Application settings managed via `pydantic-settings`. Loads environment variables for database URLs, JWT keys, CORS origins, AWS parameters, AI provider toggles, and demo flags.
* **`app/core/database.py`**: Async database session factory. Initializes `create_async_engine`, configures sessionmaker with `expire_on_commit=False`, defines dialect helpers, and provides the `get_db()` dependency.
* **`app/core/security.py`**: Cryptographic utilities and password hashing harnesses.

### 5.4.3 Relational ORM Models (`apps/api/app/models/`)
* **`app/models/base.py`**: Base declarative class with standard audit mixins (`id` UUID primary key, `created_at`, `updated_at`).
* **`app/models/organization.py`**: `Organization` model representing the top-level multi-tenant boundary.
* **`app/models/account.py`**: `CloudAccount` and `CloudRegion` models representing cloud provider billing and regional structures.
* **`app/models/resource.py`**: `CloudResource` and `Tag` models representing provisioned cloud assets with arbitrary JSON specifications.
* **`app/models/cost.py`**: `CostRecord` and `CostSnapshot` models storing daily line-item and aggregate spend numbers with 4-decimal precision (`Numeric(18, 4)`).
* **`app/models/telemetry.py`**: `ResourceMetricObservation` model storing CloudWatch operational metrics, sample counts, and calculated percentiles.
* **`app/models/anomaly.py`**: `AnomalyRecord` model storing detected statistical anomalies, severity scores, and attribution metadata.
* **`app/models/optimization.py`**: `WasteFinding`, `OptimizationOpportunity`, and `Recommendation` models storing detected cloud waste, rightsizing proposals, and compatibility rules.
* **`app/models/forecast.py`**: `ForecastSnapshot` model storing statistical forward-looking spend projections and confidence intervals.
* **`app/models/scenario.py`**: `Scenario` model storing architectural what-if simulation parameters, target resources, and estimated savings.
* **`app/models/ai.py`**: `AIInteraction` model storing user questions, query intent, evidence packages, raw LLM outputs, canonical SHA-256 hashes, and numerical validation results.

### 5.4.4 Pydantic Schemas (`apps/api/app/schemas/`)
* **`app/schemas/common.py`**: Common response envelopes, pagination schemas, and currency representations.
* **`app/schemas/dashboard.py`**: High-level executive KPI rollups, spend velocity metrics, and critical alert lists.
* **`app/schemas/spend.py`**: Time-series spend requests, dimension breakdown schemas, and service-level aggregation responses.
* **`app/schemas/resource.py`**: Resource detail schemas, inventory filters, and tag representations.
* **`app/schemas/telemetry.py`**: Metric query schemas, observation request/response models, and quality evaluation summaries.
* **`app/schemas/anomaly.py`**: Anomaly detection filters, severity overrides, and status transition schemas.
* **`app/schemas/optimization.py`**: Opportunity lists, recommendation detail models, and implementation plan schemas.
* **`app/schemas/forecast.py`**: Forecast horizon parameters, confidence bounds, and growth rate assumptions.
* **`app/schemas/scenario.py`**: Simulation configuration payloads, architectural change definitions, and financial impact summaries.
* **`app/schemas/intelligence.py`**: Engine run triggers, baseline execution summaries, and health statuses.
* **`app/schemas/analytics.py`**: Driver attribution responses, regime decomposition summaries, HHI concentration indices, and capacity headroom models.
* **`app/schemas/integrations.py`**: AWS connection configurations, permission probe summaries, and sync job execution logs.
* **`app/schemas/ai.py`**: Natural language question requests, AI answer responses, evidence citations, and numeric claim verification schemas.

### 5.4.5 Data Repositories (`apps/api/app/repositories/`)
* **`app/repositories/base.py`**: Generic base repository defining typed async CRUD operations with mandatory tenant scoping.
* **`app/repositories/organization.py`**: Organization tenant queries and slug lookups.
* **`app/repositories/account.py`**: Cloud account and region lookups scoped by tenant.
* **`app/repositories/resource.py`**: Filtered inventory queries with dynamic JSON specification parsing.
* **`app/repositories/cost.py`**: High-performance time-series cost queries, aggregation by service/account/region, and period-over-period delta calculations.
* **`app/repositories/anomaly.py`**: Anomaly persistence, resolution tracking, and severity sorting.
* **`app/repositories/optimization.py`**: Opportunity queries, recommendation lookups, and mutual exclusivity checking.
* **`app/repositories/forecast.py`**: Forecast snapshot storage and retrieval.
* **`app/repositories/scenario.py`**: Scenario persistence and parameter modification tracking.
* **`app/repositories/audit.py`**: Immutable audit event logging for platform security and compliance.

### 5.4.6 Application Services (`apps/api/app/services/`)
* **`app/services/tenant.py`**: Tenant lifecycle management and organizational context resolution.
* **`app/services/dashboard.py`**: Aggregates top-level KPI metrics, month-to-date spend, forecast trajectories, and urgent alerts.
* **`app/services/spend.py`**: Manages spend explorer queries, dimensional aggregations, and daily time-series generation.
* **`app/services/resource.py`**: Manages resource catalog queries, inventory filtering, and detail extraction.
* **`app/services/telemetry.py`**: Service managing ingestion, retrieval, and quality assessment of operational hardware telemetry.
* **`app/services/anomaly.py`**: Manages anomaly workflows, manual dismissal, and notification dispatching.
* **`app/services/optimization.py`**: Coordinates waste detection reviews and recommendation delivery.
* **`app/services/forecast.py`**: Coordinates forward-looking projection runs across 30, 60, and 90-day horizons.
* **`app/services/scenario.py`**: Orchestrates what-if scenario simulations, applying architectural changes against baseline costs.
* **`app/services/intelligence.py`**: Orchestrates Phase 5 baseline recalculations and rule-based waste detection runs.
* **`app/services/analytics.py`**: Orchestrates Phase 6 advanced analytics, driver attribution, volatility metrics, and portfolio modeling.
* **`app/services/integrations.py`**: Coordinates cloud integration lifecycles, permission verification, and background synchronization jobs.

### 5.4.7 API Routing Layer (`apps/api/app/api/v1/`)
* **`app/api/v1/router.py`**: Master API router aggregating all v1 sub-routers under `/api/v1`.
* **`app/api/v1/health.py`**: Liveness (`/health`) and readiness (`/ready`) endpoints verifying database connectivity.
* **`app/api/v1/dashboard.py`**: Endpoints delivering aggregated executive dashboard data.
* **`app/api/v1/spend.py`**: Spend exploration endpoints supporting dynamic grouping by service, account, region, and tags.
* **`app/api/v1/resources.py`**: Resource catalog endpoints with detail retrieval and telemetry attachment.
* **`app/api/v1/telemetry.py`**: Telemetry observation ingestion and query endpoints.
* **`app/api/v1/anomalies.py`**: Anomaly detection endpoints and status update routes.
* **`app/api/v1/optimization.py`**: Cost optimization and recommendation endpoints.
* **`app/api/v1/forecast.py`**: Spend forecasting endpoints.
* **`app/api/v1/scenarios.py`**: Interactive scenario creation and simulation execution endpoints.
* **`app/api/v1/intelligence.py`**: Endpoints triggering core intelligence runs and baseline updates.
* **`app/api/v1/analytics.py`**: Advanced analytics routes (cost drivers, trends, regimes, HHI concentration, capacity headroom).
* **`app/api/v1/integrations.py`**: AWS integration management, permission testing, and sync trigger endpoints.
* **`app/api/v1/ai.py`**: Natural language conversational endpoints (`/ai/ask`, `/ai/interactions`).
* **`app/api/v1/accounts.py`**: Cloud account inventory and configuration endpoints.

### 5.4.8 Deterministic Intelligence Engine (`apps/api/app/intelligence/`)
* **`app/intelligence/constants.py`**: Baseline thresholds, minimum sample sizes (7 days), and Z-score triggers ($Z > 2.5$).
* **`app/intelligence/types.py`**: Typed internal dataclasses for baseline observations, anomaly candidates, and waste findings.
* **`app/intelligence/models.py`**: Internal calculation result models.
* **`app/intelligence/baseline/calculator.py`**: Implements 14d, 30d, and 60d rolling mean, standard deviation, and median calculations.
* **`app/intelligence/baseline/engine.py`**: Evaluates baseline updates across historical spend records.
* **`app/intelligence/anomaly/detector.py`**: Evaluates daily spend against statistical baselines to identify anomalies.
* **`app/intelligence/anomaly/classifier.py`**: Classifies anomalies into operational categories (runaway job, traffic surge, configuration error).
* **`app/intelligence/waste/detector.py`**: Coordinates waste detection across all active rule sets.
* **`app/intelligence/waste/rules.py`**: Rule definitions for unattached EBS volumes, idle RDS instances, unattached IPs, and obsolete snapshots.
* **`app/intelligence/waste/calculators.py`**: Calculates unblended monthly waste amounts from resource specifications and rate cards.
* **`app/intelligence/recommendation/engine.py`**: Transforms waste findings and rightsizing opportunities into structured recommendations.
* **`app/intelligence/recommendation/rules.py`**: Action rules mapping waste types to operational remediation steps.
* **`app/intelligence/recommendation/calculators.py`**: Calculates net monthly savings, risk ratings, and implementation effort.
* **`app/intelligence/orchestration/engine.py`**: Master coordinator running the end-to-end Phase 5 intelligence pipeline.

### 5.4.9 Advanced Analytics Subsystem (`apps/api/app/analytics/`)
* **`app/analytics/constants.py`**: Volatility thresholds ($CV \ge 0.15$), HHI concentration boundaries ($1500, 2500$), and trend delta gates ($\pm 3.0\%$).
* **`app/analytics/types.py`**: Internal dataclasses for driver attributions, volatility metrics, and portfolio models.
* **`app/analytics/drivers/analyzer.py`**: Decomposes total cost deltas across Service, Account, Resource, and Region dimensions.
* **`app/analytics/drivers/attribution.py`**: Computes dual contribution metrics (Absolute Contribution % and Net Change Contribution %).
* **`app/analytics/trends/analyzer.py`**: Evaluates time-series directionality with strict precedence rules.
* **`app/analytics/trends/volatility.py`**: Calculates sample standard deviation and Coefficient of Variation ($CV$).
* **`app/analytics/regimes/classifier.py`**: Classifies spend behavior into deterministic regimes (`SPIKE`, `RECOVERY`, `ELEVATED`, `NORMAL`).
* **`app/analytics/concentration/hhi.py`**: Implements the Herfindahl-Hirschman Index calculation over service spend distribution.
* **`app/analytics/efficiency/headroom.py`**: Calculates observed hardware capacity headroom ($100\% - p95$).
* **`app/analytics/scenarios/engine.py`**: Simulates architectural what-if modifications against baseline spend.
* **`app/analytics/optimization/portfolio.py`**: Analyzes optimization portfolios, detects mutual exclusivity, and filters conflicting recommendations.

### 5.4.10 Cloud Ingestion Subsystem (`apps/api/app/integrations/`)
* **`app/integrations/constants.py`**: Required AWS IAM permissions, probe thresholds, and synchronization timeouts.
* **`app/integrations/types.py`**: Typed payloads for normalized AWS billing and resource records.
* **`app/integrations/safety.py`**: AST-based static safety scanner verifying zero mutating AWS SDK calls.
* **`app/integrations/client_factory.py`**: Request-scoped AWS client factory executing `sts:AssumeRole` with sanitized in-memory credential lifecycles.
* **`app/integrations/authenticator.py`**: Permission prober testing STS, Cost Explorer, EC2, RDS, S3, and EKS access.
* **`app/integrations/cost_explorer.py`**: Dual-path Cost Explorer adapter implementing 90-day aggregated and 14-day resource-level queries with graceful degradation.
* **`app/integrations/resources.py`**: Discovers and normalizes live EC2, RDS, S3, and EBS infrastructure metadata.
* **`app/integrations/cloudwatch.py`**: Ingests operational metric statistics from AWS CloudWatch.
* **`app/integrations/normalizer.py`**: Converts raw AWS JSON payloads into canonical Atlas relational models.
* **`app/integrations/sync.py`**: Synchronization coordinator managing sync jobs, transaction boundaries, and error provenance.

### 5.4.11 AI Explanation Subsystem (`apps/api/app/ai/`)
* **`app/ai/constants.py`**: Epistemic classes, token limits, verification tolerance ($\pm 1.0\%$), and intent categories.
* **`app/ai/types.py`**: Dataclasses for evidence packages, citations, validation results, and AI responses.
* **`app/ai/models.py`**: Schemas for conversational requests and structured answers.
* **`app/ai/contracts.py`**: Explicit structural contracts for BoundedContext, EvidencePackage, AICandidateAnswer, and AIAnswer.
* **`app/ai/context/budget.py`**: Manages token limits, pruning lower-priority evidence while preserving critical financial facts.
* **`app/ai/context/builder.py`**: Compiles structured evidence packages from deterministic database queries.
* **`app/ai/context/hasher.py`**: Computes canonical, deterministic SHA-256 hashes of assembled evidence packages.
* **`app/ai/context/sanitizer.py`**: Sanitizes user questions against prompt-injection attacks and instruction override attempts.
* **`app/ai/prompts/builder.py`**: Generates strict system prompts enforcing epistemic rules, zero-mutation mandates, and citation formatting.
* **`app/ai/prompts/rules.py`**: The 12 epistemic prompt rules prohibiting extrapolation, hallucination, and confidence metrics.
* **`app/ai/prompts/templates.py`**: Base system and user prompt templates.
* **`app/ai/providers/base.py`**: Abstract base class defining the AI provider interface.
* **`app/ai/providers/mock_provider.py`**: Deterministic offline mock provider delivering verified responses for Golden Scenarios A–J without external network access.
* **`app/ai/providers/openai_provider.py`**: Production OpenAI provider handling rate limits, timeouts, and JSON-mode structured output.
* **`app/ai/providers/exceptions.py`**: AI provider error hierarchy distinguishing network timeouts, rate limits, and schema violations.
* **`app/ai/retrieval/scope.py`**: Resolves time windows, account IDs, and service scopes from user queries.
* **`app/ai/retrieval/query_router.py`**: Classifies query intent (`WHY_SPEND_CHANGED`, `EXPLAIN_ANOMALY`, `EXPLAIN_RECOMMENDATION`, `SUMMARIZE_PORTFOLIO`, `EVALUATE_SCENARIO`, `GENERAL_INQUIRY`).
* **`app/ai/retrieval/evidence_retriever.py`**: Deterministic repository queries fetching verified financial, anomaly, and optimization evidence across 7 domains.
* **`app/ai/retrieval/freshness.py`**: Evaluates data freshness, sync recency, and epistemic staleness.
* **`app/ai/validation/gate.py`**: 8-gate response validator verifying candidates against evidence packages.
* **`app/ai/validation/claim_extractor.py`**: Regex and AST-based extraction of claimed monetary and percentage values.
* **`app/ai/validation/tolerance.py`**: Mathematical implementation of the $\pm 1.0\%$ relative error tolerance check with zero-baseline safeguards.
* **`app/ai/validation/citation_validator.py`**: Verifies that every cited evidence ID exists in the authoritative evidence package.
* **`app/ai/validation/epistemic_gate.py`**: Enforces the epistemic ceiling, preventing the model from upgrading inferred or projected claims to observed facts.
* **`app/ai/orchestration/pipeline.py`**: End-to-end execution pipeline with controlled one-shot regeneration.
* **`app/ai/orchestration/engine.py`**: Master AI coordinator.
* **`app/ai/orchestration/session_manager.py`**: Manages conversational sessions and context windows.

### 5.4.12 Synthetic Demo Subsystem (`apps/api/app/demo/`)
* **`app/demo/generator.py`**: Mathematical generator simulating realistic cloud workloads, seasonality, growth trends, and random variance.
* **`app/demo/scenarios.py`**: Pre-seeded anomalies, waste findings, and architectural optimization opportunities.
* **`app/demo/seeder.py`**: Database seeding coordinator executing transactional insertion and cleanup of demo datasets.
* **`app/demo/fixtures.py`**: Canonical resource inventory for *Nexora Labs Inc* (58 resources across 3 accounts).
* **`app/demo/events.py`**: Timeline definitions for seeded cost surges and operational anomalies.

### 5.4.13 Backend Test Suites (`apps/api/tests/` — 277 Tests)
The entire backend test suite passes with **277 passed, 0 failures**:
* Core Framework: `test_health.py`, `test_config.py`, `test_models.py`, `test_repositories.py`, `test_migrations.py`, `test_api_v1.py`.
* Demo Engine: `test_demo.py`.
* Intelligence Engine (Phase 5): `test_intelligence_baseline.py`, `test_intelligence_anomaly.py`, `test_intelligence_waste.py`, `test_intelligence_recommendation.py`, `test_intelligence_rediscovery.py`, `test_intelligence_contracts.py`, `test_intelligence_engine.py`.
* Advanced Analytics (Phase 6): `test_analytics_drivers.py`, `test_analytics_trends.py`, `test_analytics_concentration.py`, `test_analytics_efficiency.py`, `test_analytics_scenarios.py`, `test_analytics_portfolio.py`, `test_phase6_analytics_world.py`.
* AWS Ingestion (Phase 7): `test_aws_safety.py` (AST scanner), `test_aws_adapters.py`, `test_aws_sync.py`, `test_aws_ce_degradation.py`, `test_aws_disappearance.py`, `test_source_isolation.py`, `test_phase7_aws_ingestion_world.py`.
* Operational Telemetry (Phase 8): `test_cloudwatch_adapters.py`, `test_telemetry_sync.py`, `test_telemetry_quality.py`, `test_telemetry_mapping.py`, `test_operational_evidence.py`, `test_production_intelligence.py`, `test_phase8_production_intelligence_world.py`.
* AI Subsystem (Phase 9 M1–M4): `test_ai_contracts.py`, `test_ai_question_classifier.py`, `test_ai_scope_authorization.py`, `test_ai_evidence_retrieval.py`, `test_ai_freshness.py`, `test_ai_evidence_package.py`, `test_ai_context_builder.py`, `test_ai_context_budget.py`, `test_ai_sanitization.py`, `test_ai_providers.py`, `test_ai_mock_provider.py`, `test_ai_openai_provider.py`, `test_ai_prompts.py`, `test_ai_provider_errors.py`, `test_ai_validation.py`, `test_ai_validation_gates.py`, `test_ai_validation_orchestration.py`, `test_phase9_ai_world.py`.

## 5.5 Frontend Codebase Breakdown (`apps/web/`)

### 5.5.1 Application Entry & Layout
* **`src/app/main.tsx`**: Initializes React DOM root, mounts error boundaries, and imports global stylesheet.
* **`src/app/App.tsx`**: Client-side router configuration, global state providers, and global hotkey listeners (`Ctrl + K`).
* **`src/components/AppShell.tsx`**: Master shell managing navigation sidebar, header bar, and content viewport.
* **`src/components/NavigationSpine.tsx`**: Left navigation bar featuring brand identity, status markers, and route navigation.
* **`src/components/GlobalHeader.tsx`**: Top header with environment switcher, tenant context, and search trigger.
* **`src/components/AtlasPulse.tsx`**: Heartbeat pulse confirming live backend sync health.
* **`src/components/AtlasDataStatusModal.tsx`**: Modal displaying data freshness, sync timestamps, and epistemic coverage.
* **`src/components/CommandPalette.tsx`**: Modal search dialog (`Ctrl + K`) for instant navigation and action execution.
* **`src/components/DemoBanner.tsx`**: Header alert indicating synthetic dataset active status.

### 5.5.2 Domain Components
* **`src/components/topology/CostTopology.tsx`**: 5-level deterministic hierarchical cost graph.
* **`src/components/investigation/InvestigationTrace.tsx`**: 5-stage causal spine tracing spend anomalies to root cause.
* **`src/components/optimization/DecisionRoom.tsx`**: Trade-off sliders, candidate cards, and implementation considerations.
* **`src/components/scenarios/Workbench.tsx`**: Scenario sandbox with financial reconciliation checks.
* **`src/components/ai/AskAtlasPanel.tsx`**: Conversational drawer displaying verified natural language answers and provenance.
* **`src/components/ai/AIAnswerView.tsx`**: Formatted AI response view with claim verification badges and citations.
* **`src/components/ai/AIEvidenceCitation.tsx`**: Interactive citation pill linking claims directly to cost records or anomalies.
* **`src/components/ai/ProvenanceDrawer.tsx`**: Slide-out drawer revealing raw evidence packages and SHA-256 context hashes.

### 5.5.3 UI Primitives (`src/components/ui/`)
* `Card.tsx`, `Button.tsx`, `Badge.tsx`, `Skeleton.tsx`, `EmptyState.tsx`, `AtlasMark.tsx`, `EpistemicBadge.tsx`, `EvidenceLayer.tsx`, `ObservedVsInferredCard.tsx`, `TradeOffDimensionBar.tsx`.

### 5.5.4 Pages (`src/pages/`)
* `DashboardPage.tsx`, `SpendPage.tsx`, `ChangesPage.tsx` (alias `AnomaliesPage.tsx`), `OptimizationPage.tsx`, `RecommendationDetailPage.tsx`, `ResourcesPage.tsx`, `ResourceDetailPage.tsx`, `ScenariosPage.tsx`, `ForecastPage.tsx`, `IntegrationsPage.tsx`, `SettingsPage.tsx`.

### 5.5.5 Frontend Test Suites (`apps/web/tests/` — 62 Tests)
The entire Vitest frontend test suite passes with **10 test files, 62 passed, 0 failures**:
* `app.test.tsx`: Shell rendering, route transitions, demo banner display.
* `dashboard.test.tsx`: Macro KPI strip calculation, spend velocity, anomaly integration.
* `topology.test.tsx`: Hierarchical cost topology rendering, node expansion, percentage rollups.
* `investigation.test.tsx`: Causal trace spine, driver cards, root-cause attribution.
* `optimization-workspace.test.tsx`: Portfolio hero strip, decision room, trade-off sliders, read-only boundary check.
* `resource-intelligence.test.tsx`: Telemetry sparklines, observation cards, quality score display.
* `scenarios-workbench.test.tsx`: Financial reconciliation check, what-if simulations, provenance drawer.
* `ask-atlas-console.test.tsx`: Citation pill interaction, epistemic badge display, verified answer rendering.
* `command-palette.test.tsx`: Hotkey activation, resource filtering, keyboard selection.
* `format.test.ts`: Monospace currency formatting, percentage deltas, date helpers.

---

# 6. Future Plans & Roadmap

```mermaid
flowchart LR
    P9[Phase 9: AI Explanation] --> P10[Phase 10: Controlled Execution]
    P10 --> P11[Phase 11: Multi-Cloud Unified Mesh]
    P11 --> P12[Phase 12: Provable Autonomous FinOps]
```

## 6.1 Phase 9 Completion: Milestones 5 through 8

While Milestones 1 through 4 are complete and mathematically verified:
* **Milestone 5 (API Endpoints & Session Persistence)**: Wire `AIEngine` into `/api/v1/ai/ask` and `/api/v1/ai/interactions`. Persist full interaction history to `ai_interactions` table.
* **Milestone 6 (Conversational Sessions & Multi-Turn Memory)**: Session manager tracking conversational threads with rolling token budgeting.
* **Milestone 7 (Audit Provenance & Cryptographic Export)**: Exportable audit bundles containing query, context hash, raw prompt, candidate answer, validation log, and final answer.
* **Milestone 8 (Frontend Ask Atlas Console Integration)**: Seamless connection between the React frontend `AskAtlasPanel` and the live M5 API endpoints.

## 6.2 Phase 10: Controlled Execution & IaC Pull Request Automation

Phase 10 introduces opt-in, human-in-the-loop remediation orchestration:
1. **Four-Eyes Approval Workflows**: High-impact recommendations require dual-signature approval from authorized FinOps and Engineering leads.
2. **Infrastructure-as-Code (IaC) PR Generation**: Rather than mutating cloud APIs directly, Atlas generates version-controlled Git pull requests against Terraform or Pulumi repositories.
3. **Pre-Flight Dry-Run Validation**: Simulates proposed modifications in a sandbox environment before merge.
4. **Automated Rollback Snapshots**: Generates automated rollback scripts and pre-action EBS/RDS snapshots.

## 6.3 Phase 11: Multi-Cloud Unified Mesh (GCP, Azure, Kubernetes)

Extending canonical normalization to additional cloud and container environments:
1. **Google Cloud Platform (GCP)**: Ingestion of GCP Cloud Billing BigQuery exports and Cloud Monitoring metrics via Workload Identity Federation.
2. **Microsoft Azure**: Ingestion of Azure Cost Management Exports and Azure Monitor metrics via Azure Managed Identities.
3. **Kubernetes (K8s) & Container Cost Allocation**: Native ingestion of container metrics via OpenCost or Kubecost, mapping Pod/Namespace allocations directly to Atlas canonical resources.

## 6.4 Phase 12: Provable Autonomous FinOps Agents

1. **Formal SMT Verification**: Leveraging formal methods (e.g. Z3 or TLA+) to mathematically prove that a proposed portfolio of rightsizing changes will not violate high-availability or latency SLAs.
2. **Dynamic Commitment Balancer**: Continuous automated adjustment of Compute Savings Plans and Reserved Instances to maintain target coverage percentages ($75\%\text{--}85\%$).

---

# 7. Known Problems, Limitations & Edge Cases

### 7.1 Cloud Provider Ingestion Latency (AWS CE 24–48h Lag)
* **Problem**: AWS Cost Explorer records are delayed by 24 to 48 hours. Aggregated billing records for "today" or "yesterday" do not exist in live AWS APIs.
* **Atlas Handling**: The platform detects data freshness during ingestion. Dates within the 48-hour lag window are classified as `INFERRED` or `PROJECTED`, and a persistent freshness indicator warns users that current-day spend is estimated.

### 7.2 Telemetry API Rate Limits & Throttling
* **Problem**: AWS CloudWatch `GetMetricData` has strict account-level TPS limits. Querying high-frequency metrics across $> 500$ instances can trigger `ThrottlingException`.
* **Atlas Handling**: The adapter batches metric queries up to the AWS limit of 500 metrics per call, enforces exponential backoff with jitter, and caches metric observations in the database for 1 hour.

### 7.3 Zero-Telemetry Serverless Workloads
* **Problem**: Serverless resources (e.g. AWS Lambda, S3 buckets, DynamoDB tables) do not report standard CPU or Memory utilization metrics.
* **Atlas Handling**: The telemetry engine explicitly sets `epistemic_status = NOT_AVAILABLE` and `data_quality = 0` for serverless assets. Waste rules requiring hardware utilization (e.g. downscaling) are blocked from firing against serverless resources.

### 7.4 SQLite Concurrency & Locking
* **Problem**: SQLite uses database-level (or table-level in WAL mode) locking. Under high-concurrency async write loads, operations can throw `sqlite3.OperationalError: database is locked`.
* **Atlas Handling**: Atlas sets `timeout=30.0` on `aiosqlite` connections. SQLite is designated strictly for local single-developer workflows and automated CI testing. Production environments must configure PostgreSQL 16.

### 7.5 Windows Python 3.13 Alembic Path Separator Deprecation
* **Problem**: On Windows with Python 3.13, Alembic emits `DeprecationWarning: No path_separator found in configuration; falling back to legacy splitting...`.
* **Atlas Handling**: This is a non-blocking upstream cosmetic deprecation in Alembic's `config.py` that does not impact migration correctness. Migration tests explicitly pass.

### 7.6 Fixed-Point Decimal Transport Serialization
* **Problem**: Standard JSON specification lacks a fixed-point decimal type, causing standard JavaScript JSON parsers to deserialize large numbers into IEEE 754 floating-point numbers.
* **Atlas Handling**: Pydantic v2 serializes `Decimal` values cleanly, and API response schemas format critical financial figures with explicit currency codes and string representations where precision loss is unacceptable.

---

# 8. Mathematical Formulations & Formal Proofs

Every metric, baseline, and validation check in NEXORA ATLAS is mathematically defined and deterministic.

## 8.1 Spend Aggregation & Period Deltas

Total spend on day $t$ across a set of resources $R$ is:
$$C_{\text{daily}}(t) = \sum_{r \in R} c(r, t)$$
Where $c(r, t)$ is the unblended cost of resource $r$ on date $t$.

The period-over-period spend delta between current period $T_{\text{curr}}$ and preceding period $T_{\text{prev}}$ of equal duration $N$ is:
$$\Delta C = C(T_{\text{curr}}) - C(T_{\text{prev}}) = \sum_{t \in T_{\text{curr}}} C_{\text{daily}}(t) - \sum_{t \in T_{\text{prev}}} C_{\text{daily}}(t)$$

The percentage spend change is:
$$\Delta \% = \begin{cases} \frac{\Delta C}{C(T_{\text{prev}})} \times 100 & \text{if } C(T_{\text{prev}}) > 0 \\ 0.0 & \text{otherwise} \end{cases}$$

## 8.2 Dual Driver Contribution Metrics (Absolute vs Net)

To prevent misleading attribution when positive and negative deltas offset each other, Atlas computes two orthogonal contribution metrics for every driver $i$:

### 1. Absolute Contribution Percentage
Measures the share of total gross volatility attributable to driver $i$:
$$\text{Contrib}_{\text{abs}}(i) = \frac{|\Delta c_i|}{\sum_{j=1}^{M} |\Delta c_j|} \times 100$$
*Properties*:
* $0 \le \text{Contrib}_{\text{abs}}(i) \le 100\%$
* $\sum_{i=1}^{M} \text{Contrib}_{\text{abs}}(i) = 100.0\%$ (strictly conserved)

### 2. Net Change Contribution Percentage
Measures the proportion of net portfolio shift explained by driver $i$:
$$\text{Contrib}_{\text{net}}(i) = \begin{cases} \frac{\Delta c_i}{\Delta C_{\text{total}}} \times 100 & \text{if } \Delta C_{\text{total}} \ne 0 \\ 0.0 & \text{if } \Delta C_{\text{total}} = 0 \end{cases}$$
*Properties*: Can exceed $100\%$ or be negative if opposing drivers offset the net change.

## 8.3 Rolling Baselines & Statistical Z-Score Anomalies

For a financial time series $x = (x_1, x_2, \dots, x_N)$ over rolling window $N$:

### Sample Mean ($\mu$)
$$\mu = \frac{1}{N} \sum_{t=1}^{N} x_t$$

### Sample Standard Deviation ($\sigma$)
$$\sigma = \sqrt{\frac{1}{N - 1} \sum_{t=1}^{N} (x_t - \mu)^2} \quad (\text{for } N > 1)$$

### Statistical Z-Score & Severity
$$Z = \frac{c_t - \mu}{\sigma}$$
An anomaly triggers when $Z > 2.5$. The severity score is bounded in $[0, 1]$:
$$\text{Severity} = \min\left(1.0, \frac{|c_t - \mu|}{3\sigma}\right)$$

## 8.4 Volatility Index & Deterministic Trend Precedence

Spend volatility is measured using the **Coefficient of Variation ($CV$)**:
$$CV = \begin{cases} \frac{\sigma}{\mu} & \text{if } \mu > 0 \\ 0.0 & \text{otherwise} \end{cases}$$

### Trend Classification Precedence
1. **`VOLATILE`**: If $CV \ge 0.15$ ($15\%$ volatility threshold).
2. **`INCREASING`**: If $CV < 0.15$ and $\Delta \% > +3.0\%$.
3. **`DECREASING`**: If $CV < 0.15$ and $\Delta \% < -3.0\%$.
4. **`STABLE`**: If $CV < 0.15$ and $-3.0\% \le \Delta \% \le +3.0\%$.

## 8.5 Behavioral Spend Regime State Machine

Daily spend is classified using deterministic precedence:
1. **`SPIKE`**: $c_t > 1.50 \times \mu$ (exceeds baseline mean by $> 50\%$ on day $t$).
2. **`RECOVERY`**: Previous day was `SPIKE` or `RECOVERY` within last 7 days AND $c_t < c_{t-1}$.
3. **`ELEVATED`**: $c_t > 1.10 \times \mu$ for 3 or more consecutive days.
4. **`NORMAL`**: $0.90 \times \mu \le c_t \le 1.10 \times \mu$.

## 8.6 Herfindahl-Hirschman Concentration Index (HHI)

Portfolio concentration across cloud services is calculated via the **Herfindahl-Hirschman Index (HHI)**:
$$HHI = \sum_{i=1}^{K} s_i^2$$
Where $s_i$ is the percentage share of total spend for service $i$:
$$s_i = \left(\frac{C_i}{C_{\text{total}}}\right) \times 100, \quad \sum_{i=1}^{K} s_i = 100$$
* $HHI < 1,500$: **Diversified** spend profile.
* $1,500 \le HHI \le 2,500$: **Moderate Concentration**.
* $HHI > 2,500$: **High Concentration**.

## 8.7 Local Nearest Rank Telemetry Percentiles ($p95$)

Atlas computes $p95$ locally from an ascending sorted list of $N$ observed sample values $(v_1 \le v_2 \le \dots \le v_N)$ using the **Nearest Rank Method**:
$$n = \left\lceil \frac{95}{100} \times N \right\rceil, \quad p95 = v_n$$
Where $\lceil \cdot \rceil$ is the ceiling function.

## 8.8 Telemetry Sampling Coverage & Trustworthiness Scoring

Telemetry quality evaluates observed sample intervals against expected intervals over evaluation window $W$:
$$\text{Coverage Ratio} = \frac{N_{\text{observed}}}{N_{\text{expected}}}$$
Where $N_{\text{expected}} = \frac{W_{\text{seconds}}}{\text{Period}_{\text{seconds}}}$. For a 14-day window with 5-minute sampling:
$$N_{\text{expected}} = \frac{14 \times 86,400}{300} = 4,032 \text{ samples}$$

$$\text{Sufficiency} = \begin{cases} \text{SUFFICIENT} & \text{if Coverage Ratio} \ge 0.70 \text{ and Age} \le 24\text{h} \\ \text{INSUFFICIENT} & \text{otherwise} \end{cases}$$

## 8.9 Numerical Claim Verification Gate ($\pm 1.0\%$ Relative Error)

When the AI Explanation subsystem processes candidate answers, every numeric assertion $V_{\text{claimed}}$ is checked against the authoritative database evidence value $V_{\text{auth}}$:

$$\text{Relative Error} = \frac{|V_{\text{claimed}} - V_{\text{auth}}|}{|V_{\text{auth}}|} \quad (\text{for } V_{\text{auth}} \ne 0)$$

### Verification Rule
$$\text{Claim Status} = \begin{cases} \text{VERIFIED} & \text{if Relative Error} \le 0.01 \quad (\le 1.0\% \text{ tolerance}) \\ \text{FAILED} & \text{if Relative Error} > 0.01 \end{cases}$$

### Strict Zero-Baseline Invariant
If $V_{\text{auth}} = 0$, the check enforces exact equality:
$$\text{Claim Status} = \begin{cases} \text{VERIFIED} & \text{if } V_{\text{claimed}} = 0 \\ \text{FAILED} & \text{if } V_{\text{claimed}} \ne 0 \end{cases}$$

## 8.10 Annualized Financial Savings Invariant

All monthly optimization recommendations and scenario projections are annualized using the strict financial invariant:
$$\text{Savings}_{\text{annual}} = \text{Savings}_{\text{monthly}} \times 12$$

## 8.11 Cryptographic Context Hashing

To ensure immutable auditability of AI explanations, assembled evidence packages are serialized into canonical sorted JSON and cryptographically hashed:
$$\text{Context Hash} = \text{SHA-256}(\text{Canonicalize}(\text{EvidencePackage}))$$
Where $\text{Canonicalize}(J)$ enforces alphabetical key sorting, UTF-8 encoding, and zero extraneous whitespace.

---

# 9. Comprehensive Operator & Developer Manual

## 9.1 Local Development Environment Setup

### Prerequisites
* **Python**: `3.12+` (or `3.13+`)
* **Node.js**: `20+` and `npm`
* **Git**

### Step 1: Clone Repository
```bash
git clone https://github.com/nexora-atlas/nexora-atlas.git
cd "d:\Nexora Atlas"
```

### Step 2: Backend Setup (Zero-Docker Mode via SQLite)
```powershell
cd apps\api

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install backend dependencies
pip install -r requirements.txt

# Run database migrations to head
alembic upgrade head

# Seed synthetic demo data (Nexora Labs Inc - 58 resources, 90 days of spend)
python -m scripts.seed_demo

# Start the FastAPI development server with Hot Reload
python -m uvicorn app.main:app --reload --port 8000
```
*API Swagger Documentation is available at `http://localhost:8000/docs`.*

### Step 3: Frontend Setup
```powershell
cd apps\web

# Install frontend dependencies
npm install

# Start the Vite development server
npm run dev
```
*Frontend Web Application is accessible at `http://localhost:5173`.*

## 9.2 Running with Docker Compose (PostgreSQL Production)

To run the complete production stack including PostgreSQL 16:
```bash
# From repository root:
docker-compose up --build
```
This provisions:
* `postgres`: PostgreSQL 16 on port `5432` with volume persistence.
* `api`: FastAPI backend container on port `8000`.
* `web`: NGINX production static asset server on port `80`.

## 9.3 Database Migrations & Seeding Synthetic Data

```bash
cd apps/api

# Apply all migrations
alembic upgrade head

# Create a new migration revision after model changes
alembic revision --autogenerate -m "describe_changes_here"

# Seed or reset demo data
python scripts/seed_demo.py
```

## 9.4 Executing Verification Test Suites

Both test suites must be executed and confirmed passing with zero failures:

### Backend Pytest Suite (277 Tests)
```bash
cd apps/api
pytest -v
```
*Expected: `277 passed in ~70s`.*

### Frontend Vitest Suite (62 Tests)
```bash
cd apps/web
npm.cmd test -- --run
```
*Expected: `Test Files: 10 passed (10), Tests: 62 passed (62)`.*

## 9.5 Environment Variable Reference

Configured via environment variables or `.env` in `apps/api/`:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `sqlite+aiosqlite:///./atlas_dev.db` | Async SQLAlchemy database URL. Set to `postgresql+asyncpg://atlas:atlas@localhost:5432/atlas` in production. |
| `DEMO_MODE` | `true` | Enables synthetic demo data endpoints and demo banner. |
| `AI_ENABLED` | `true` | Master toggle for Phase 9 conversational AI subsystem. |
| `AI_PROVIDER` | `mock` | AI provider: `mock` (deterministic offline golden scenarios) or `openai`. |
| `OPENAI_API_KEY` | `""` | API key required when `AI_PROVIDER=openai`. |
| `OPENAI_MODEL` | `gpt-4o` | Model identifier used for natural language explanation generation. |
| `CORS_ORIGINS` | `["http://localhost:5173", "http://localhost:3000"]` | Allowed CORS origins for frontend client access. |
| `AWS_ASSUME_ROLE_ENABLED` | `false` | Enables live AWS cross-account STS AssumeRole authentication. |
| `AWS_EXTERNAL_ID_SECRET` | `""` | Shared secret used to generate external IDs for AWS trust policies. |

## 9.6 Debugging Validation Rejections & AI Auditing

When an AI explanation is rejected by the 8-Gate Response Validator:
1. Inspect the record in the `ai_interactions` table using `id` or `context_hash`.
2. Review `verification_status` (`VERIFIED`, `WARNING`, `FAILED`).
3. Check `evidence_package_json` to inspect the exact authoritative numbers supplied to the provider.
4. If a claim failed Gate 6 ($\pm 1.0\%$ tolerance gate), compare `claimed_value` against `actual_value` in the validation error details.
5. In offline development mode, ensure queries match one of the Golden Scenarios A–J defined in `app/ai/providers/mock_provider.py`.

---

> **NEXORA ATLAS ARCHITECTURAL COMMITMENT**:  
> *Every financial dollar reported is grounded in immutable evidence. Every recommendation is mathematically validated. Zero cloud infrastructure is ever modified without human authorization.*
