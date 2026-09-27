# NEXORA ATLAS — UI/UX Master Specification

> **The Technology Financial Intelligence Command Center**  
> *"Know where technology money is going, why it changed, what the evidence says, and what to investigate next."*  
> Specification Version: `3.1.0` | Target Audience: Antigravity Engineering, Frontend Architects, FinOps Product Designers

---

## Table of Contents

1. [Product Vision & Core UX Philosophy](#1-product-vision--core-ux-philosophy)
2. [Design Tokens & Visual Language](#2-design-tokens--visual-language)
3. [The 3-Level Visual Hierarchy](#3-the-3-level-visual-hierarchy)
4. [Application Shell & Global Chrome](#4-application-shell--global-chrome)
   - 4.1 [Restructured Navigation Hierarchy](#41-restructured-navigation-hierarchy)
   - 4.2 [System Context Top Bar & Health Flyout](#42-system-context-top-bar--health-flyout)
   - 4.3 [Global Contextual Ask Atlas Architecture](#43-global-contextual-ask-atlas-architecture)
   - 4.4 [Global Command Palette (`Ctrl + K` / `Cmd + K`)](#44-global-command-palette-ctrl--k--cmd--k)
   - 4.5 [Refined Persistent Demo Indicator](#45-refined-persistent-demo-indicator)
5. [Page-by-Page Specifications & Wireframes](#5-page-by-page-specifications--wireframes)
   - 5.1 [Command Center (`/dashboard`) — The Flagship Experience](#51-command-center-dashboard--the-flagship-experience)
   - 5.2 [Spend Explorer (`/spend`) — Investigation & Progressive Drill-Down](#52-spend-explorer-spend--investigation--progressive-drill-down)
   - 5.3 [Changes (`/changes`, alias `/anomalies`) — What Happened](#53-changes-changes-alias-anomalies--what-happened)
   - 5.4 [Optimization Workspace (`/optimization`) — Addressable Opportunities](#54-optimization-workspace-optimization--addressable-opportunities)
   - 5.5 [Recommendation Detail (`/optimization/:id`) — Engineering Case File](#55-recommendation-detail-optimizationid--engineering-case-file)
   - 5.6 [Resource Intelligence (`/resources/:id`) — Synthesis & Telemetry](#56-resource-intelligence-resourcesid--synthesis--telemetry)
   - 5.7 [Scenarios Simulation Workbench (`/scenarios`) — Architecture Sandbox](#57-scenarios-simulation-workbench-scenarios--architecture-sandbox)
   - 5.8 [Forecast (`/forecast`) — Historical vs Projected Trajectory](#58-forecast-forecast--historical-vs-projected-trajectory)
   - 5.9 [Integrations (`/integrations`) — Trust Boundary Control Room](#59-integrations-integrations--trust-boundary-control-room)
   - 5.10 [Ask Atlas Drawer — The Research Result Console](#510-ask-atlas-drawer--the-research-result-console)
6. [Signature Components Anatomy & Behavioral Rules](#6-signature-components-anatomy--behavioral-rules)
   - 6.1 [The Evidence Layer (`EvidenceLayer`)](#61-the-evidence-layer-evidencelayer)
   - 6.2 [Multi-Dimensional Trade-Off Bars (`TradeOffDimensionBar`)](#62-multi-dimensional-trade-off-bars-tradeoffdimensionbar)
   - 6.3 [Epistemic Classification Badges (`EpistemicBadge`)](#63-epistemic-classification-badges-epistemicbadge)
   - 6.4 [Interactive Evidence Citation Pills (`EvidenceCitationPill`)](#64-interactive-evidence-citation-pills-evidencecitationpill)
   - 6.5 [Telemetry Quality & Sufficiency Callouts](#65-telemetry-quality--sufficiency-callouts)
   - 6.6 [Evidence-Grounded Empty States](#66-evidence-grounded-empty-states)
7. [Micro-Interactions, Transitions & Chart Rules](#7-micro-interactions-transitions--chart-rules)
8. [Responsive Viewport Adaptations (1440px to Mobile)](#8-responsive-viewport-adaptations-1440px-to-mobile)
9. [Step-by-Step Implementation Blueprint for Antigravity](#9-step-by-step-implementation-blueprint-for-antigravity)

---

# 1. Product Vision & Core UX Philosophy

NEXORA ATLAS transforms from a technically impressive set of discrete cards into **The Technology Financial Intelligence Command Center**.

The interface rejects the passive paradigm:
> *"Here are your cloud cost dashboards."*

And enforces an active, analytical inquiry:
> **"Here is what changed, why it changed, what the evidence says, what it means financially, and what you can investigate next."**

### The Core UX Grammar
Every analytical surface in Atlas strictly executes this continuous chain of reasoning:

```text
MONEY → CHANGE → CAUSE → EVIDENCE → OPPORTUNITY → SCENARIO → DECISION
```

### Visual Personality
* **Inspiration**: Bloomberg Terminal × Palantir Foundry × Linear × Modern Infrastructure Control Systems.
* **Core Temperament**: Quietly powerful, sober, surgically precise, high-density.
* **Anti-Pattern**: No neon "cyberpunk" glowing cards, no arbitrary synthetic scores, no noisy decorative gradients. Every visual element maps to authoritative data or epistemic status.

---

# 2. Design Tokens & Visual Language

Atlas utilizes a cohesive, mathematically grounded design system designed for dark workspaces and high data density.

### 2.1 Color Tokens

```css
/* Surface & Background Hierarchy */
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

/* Semantic Accents (Restrained — strictly reserved for status & change) */
--atlas-positive:     #10B981; /* Cost reductions, healthy state, verified claims */
--atlas-warning:      #F59E0B; /* Anomalies, elevated regimes, moderate risk */
--atlas-critical:     #EF4444; /* Cost spikes, runaway spend, high risk */
--atlas-info:         #38BDF8; /* General discovery, links, active filters */
--atlas-primary:      #0EA5E9; /* Brand cyan-blue primary interaction accent */

/* Epistemic Class Badge Palette */
--epistemic-observed:       bg-[#1E293B] text-[#94A3B8] border-[#334155];
--epistemic-derived:        bg-[#0C2A4A] text-[#7DD3FC] border-[#0284C7]/40;
--epistemic-inferred:       bg-[#3D2206] text-[#FCD34D] border-[#D97706]/40;
--epistemic-assumed:        bg-[#281347] text-[#C4B5FD] border-[#7C3AED]/40;
--epistemic-projected:      bg-[#082F49] text-[#38BDF8] border-[#0284C7];
--epistemic-not-available:  bg-[#181E29] text-[#64748B] border-[#334155]/40;
```

### 2.2 Typography System

Atlas uses a strict dual-font typography contract:

1. **Interface Typography (`Inter`, system fallback)**:
   - Headings, navigation labels, narrative explanations, buttons, modal titles.
   - Weights: `font-normal` (400), `font-medium` (500), `font-semibold` (600), `font-bold` (700).
2. **Data Typography (`JetBrains Mono`, `ui-monospace`, monospace)**:
   - All currency values (`₹12,542.38`), percentage deltas (`+18.4%`), resource IDs (`i-0a8b9c7d`), instance types (`m5.4xlarge`), AWS account numbers, sample counts, and telemetry statistics.
   - Eliminates layout shifting and enables instant vertical decimal alignment across tabular rows.

### 2.3 Structural Rhythm & Border Radii
* Card Radius: `rounded-lg` (8px).
* Button / Pill Radius: `rounded-md` (6px) or `rounded-full` (for citation pills).
* Spacing Scale: Strict 4px grid (`p-1` = 4px, `p-2` = 8px, `p-3` = 12px, `p-4` = 16px, `p-6` = 24px).

---

# 3. The 3-Level Visual Hierarchy

Every screen in Atlas must adhere to three clearly differentiated visual levels. Never render a screen as a flat wall of uniform cards.

```text
┌────────────────────────────────────────────────────────────────────────┐
│ LEVEL 1: WHAT MATTERS (Large / High Contrast)                          │
│                                                                        │
│   ₹12.5L             +8.4%            ₹4.60L            4              │
│   Monthly Run Rate   vs Prev Period   Addressable Opp   Anomalies      │
├────────────────────────────────────────────────────────────────────────┤
│ LEVEL 2: WHY (Medium / Structured Grouping)                            │
│                                                                        │
│   • EC2 Production Compute (+₹2.14L / month)                           │
│   • GPU Training Cluster (+₹1.21L / month)                             │
│   • S3 Analytics Warehouse (+₹0.68L / month)                           │
├────────────────────────────────────────────────────────────────────────┤
│ LEVEL 3: EVIDENCE (Dense / Monospace / Restrained Metadata)            │
│                                                                        │
│   CPU p95: 11.2% │ Coverage: 94% │ Window: 14d │ OBSERVED: CloudWatch  │
└────────────────────────────────────────────────────────────────────────┘
```

---

# 4. Application Shell & Global Chrome

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ NEXORA ATLAS  Nexora Labs Inc. ▾  90D · INR   Search ⌘K   Ask Atlas  ● Conn │
├───────────────┬─────────────────────────────────────────────────────────────┤
│ OVERVIEW      │                                                             │
│ ◉ Command     │                                                             │
│               │                                                             │
│ FINANCIAL     │                                                             │
│ ◌ Spend       │                                                             │
│ ◌ Forecast    │                      MAIN WORKSPACE                         │
│               │                      (Scrollable Content)                   │
│ INTELLIGENCE  │                                                             │
│ ◌ Changes  (4)│                                                             │
│ ◌ Optimize (7)│                                                             │
│ ◌ Scenarios   │                                                             │
│               │                                                             │
│ INFRASTRUCT.  │                                                             │
│ ◌ Resources   │                                                             │
│ ◌ Integrations│                                                             │
│               │                                                             │
│ SYSTEM        │                                                             │
│ ◌ Settings    │                                                             │
│ ───────────── │                                                             │
│ AWS: 3 accts  │                                                             │
└───────────────┴─────────────────────────────────────────────────────────────┘
```

## 4.1 Restructured Navigation Hierarchy

The sidebar is reorganized around logical user intent:

```typescript
export interface NavSection {
  title: string;
  items: NavItemConfig[];
}

export const navSections: NavSection[] = [
  {
    title: 'OVERVIEW',
    items: [
      { name: 'Command Center', path: '/dashboard', icon: LayoutDashboard },
    ],
  },
  {
    title: 'FINANCIAL',
    items: [
      { name: 'Spend', path: '/spend', icon: BarChart3 },
      { name: 'Forecast', path: '/forecast', icon: TrendingUp },
    ],
  },
  {
    title: 'INTELLIGENCE',
    items: [
      { name: 'Changes', path: '/changes', icon: AlertTriangle, badgeKey: 'anomalies' },
      { name: 'Optimization', path: '/optimization', icon: Zap, badgeKey: 'optimization' },
      { name: 'Scenarios', path: '/scenarios', icon: GitFork },
    ],
  },
  {
    title: 'INFRASTRUCTURE',
    items: [
      { name: 'Resources', path: '/resources', icon: Server },
      { name: 'Integrations', path: '/integrations', icon: CloudCog },
    ],
  },
  {
    title: 'SYSTEM',
    items: [
      { name: 'Settings', path: '/settings', icon: Settings },
    ],
  },
];
```

> [!NOTE]
> `/anomalies` remains configured as a backwards-compatible redirect to `/changes`.

## 4.2 System Context Top Bar & Health Flyout

The top bar is an active **System Context Bar**:
* **Organization Switcher**: `Nexora Labs Inc. ▾` with active environment tag (`PROD`).
* **Time & Currency Scope**: `90 DAYS · INR (₹) · Asia/Kolkata`.
* **Global Search Box**: Centered shortcut trigger with `<kbd>Ctrl</kbd> + <kbd>K</kbd>`.
* **Global Ask Atlas Activator**: Distinct button with sparkle icon opening the contextual AI drawer.
* **System Trust Pill**: `● Connected` indicator. Clicking toggles the **Atlas Data Status Modal**:

```text
┌──────────────────────────────────────────────────────────────┐
│ ATLAS DATA STATUS & TRUST BOUNDARY                           │
├──────────────────────────────────────────────────────────────┤
│ Cloud Connection                                             │
│ Provider: AWS (3 Accounts · 58 Active Resources)             │
│ Authentication: STS AssumeRole (Request-Scoped Ephemeral)    │
│                                                              │
│ Ingestion Provenance                                         │
│ Cost Data:       ● Current (Last sync: 8 min ago)            │
│ Telemetry:       ● Healthy (Coverage: 94%, 2h latency)       │
│ Intelligence:    ● Evaluated (Evaluated 12 min ago)          │
│ AI Verification: ● Active (±1.0% Numeric Tolerance Gate)     │
│                                                              │
│ Trust Boundary Enforcement                                   │
│ ✓ Read-Only Constraint: 0 mutating AWS API calls             │
│ ✓ AST Static Analysis Verification: PASSING                  │
└──────────────────────────────────────────────────────────────┘
```

## 4.3 Global Contextual Ask Atlas Architecture

**Ask Atlas is never trapped on a single page.** It is a global slide-out drawer (`AskAtlasDrawer`) accessible via:
1. Top bar `Ask Atlas` button.
2. Global shortcut `Ctrl + J` / `Cmd + J`.
3. In-context buttons on charts, tables, resources, and recommendations (e.g. `[Ask Atlas why this spiked]`).

When invoked from a specific view, the drawer automatically inherits the active context (e.g. current resource ID, service name, or recommendation).

## 4.4 Global Command Palette (`Ctrl + K` / `Cmd + K`)
Allows fuzzy search across all 58 resources, 7 recommendations, 4 anomalies, and direct navigation shortcuts.

## 4.5 Refined Persistent Demo Indicator
Replaces large banners with an elegant persistent status pill in the top bar:
`[ DEMO ENVIRONMENT · Synthetic AWS · 58 Resources · 90 Days ]`.

---

# 5. Page-by-Page Specifications & Wireframes

---

## 5.1 Command Center (`/dashboard`) — The Flagship Experience

The Command Center is the focal point of the platform. It immediately answers:
**"What is our position, what shifted, what drove it, and what needs investigation?"**

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ COMMAND CENTER                                                              │
│ Technology Financial Position · September 2026                              │
│                                                                             │
│ ┌──────────────────┬──────────────────┬──────────────────┬────────────────┐ │
│ │ ₹12.50L          │ ↑ 8.4%           │ ₹4.60L           │ 4              │ │
│ │ Monthly Run Rate │ vs prev period   │ Addressable Opp. │ Anomalies      │ │
│ └──────────────────┴──────────────────┴──────────────────┴────────────────┘ │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ MONTHLY TECHNOLOGY SPEND TRAJECTORY                         90-Day View │ │
│ │                                                                         │ │
│ │ ₹15L ┤                                       ▲ Spiked (+54.8%)          │ │
│ │      │                              ╭────────● GPU training             │ │
│ │ ₹12L ┤                    ╭─────────╯                                   │ │
│ │      │         ╭──────────╯                                             │ │
│ │  ₹9L ┤─────────╯                                                        │ │
│ │      └───────────────────────────────────────────────────────────────   │ │
│ │        Jun 25           Jul 15           Aug 05          Sep 20         │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ ┌──────────────────────────────────────────────┬──────────────────────────┐ │
│ │ WHAT CHANGED (Primary Driver)                │ TOP COST DRIVERS         │ │
│ │                                              │                          │ │
│ │ EC2 · Production Compute                     │ EC2             +₹2.14L  │ │
│ │ +₹2.14L / month (+18.7%)                     │ GPU Workloads   +₹1.21L  │ │
│ │                                              │ S3 Analytics    +₹0.68L  │ │
│ │ Root Cause Attribution                       │ RDS Primary     +₹0.41L  │ │
│ │ Production API compute auto-scaling cluster. │ EKS Clusters    +₹0.16L  │ │
│ │                                              │                          │ │
│ │ [Show Evidence (Usage ↑ 38%, p95: 11.2%) ▾]  │ Portfolio Concentration  │ │
│ │                                              │ HHI: 2,640 (High)        │ │
│ │                                              │ EC2 & RDS represent 68%  │ │
│ │                                              │                          │ │
│ │ [Investigate Driver →]   OBSERVED · DERIVED  │ [Explore Spend Drivers →]│ │
│ └──────────────────────────────────────────────┴──────────────────────────┘ │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ NEEDS ATTENTION (Prioritized Investigation Queue)                       │ │
│ │                                                                         │ │
│ │ 01  Production API Cluster          +38.2% cost surge    [Investigate →]│ │
│ │     Anomaly detected · Egress & compute scaling · 94% coverage          │ │
│ │                                                                         │ │
│ │ 02  GPU Training Environment        +52.0% sustained     [Investigate →]│ │
│ │     Unplanned fine-tuning run · Account: aws-data-03                    │ │
│ │                                                                         │ │
│ │ 03  S3 Analytics Data Lake          +122.2% growth       [Investigate →]│ │
│ │     Unindexed parquet exports · Storage growth anomaly                  │ │
│ │                                                                         │ │
│ │ 04  Staging Pre-Prod Cluster        +61.9% inefficiency  [Investigate →]│ │
│ │     Oversized compute nodes · Idle off-hours                             │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Breakdown
1. **Financial Position Header**: 4 key figures with monospace values and change badges.
2. **Spend Trajectory Chart**: Interactive Recharts time series with plotted anomaly markers (red/amber pins). Hovering reveals tooltip with exact date, delta %, service, and an `[Investigate]` deep link.
3. **"What Changed?" Card**: Highlights the #1 cost driver calculated by Phase 6 analytics (`absolute_contribution_pct`) with progressive disclosure toggle for underlying telemetry.
4. **Top Drivers Summary**: Monospace table displaying net changes and spend concentration index (HHI, kept subordinate as a secondary descriptive diagnostic metric).
5. **Needs Attention Queue**: Clean list showing the top 4 critical anomalies and waste findings, with zero arbitrary scores.

---

## 5.2 Spend Explorer (`/spend`) — Investigation & Progressive Drill-Down

The Spend page is an interactive investigative workbench supporting 4-level progressive drill-down:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ SPEND EXPLORER                                                              │
│ Technology Financial History & Attribution                                  │
│                                                                             │
│ Total Spend: ₹36.83L (90 Days) │ PoP Delta: +6.2% │ View: [Service] Account │
│ Metric: [Spend] [Δ Spend] [% Change] [7D Avg] [14D Avg] [30D Avg]           │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ INTERACTIVE MULTI-SERIES SPEND CHART                                    │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ PROGRESSIVE DRILL-DOWN INVESTIGATION                                        │
│ Breadcrumb: All Services > EC2 > Production                                │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ SUB-ALLOCATION BREAKDOWN                                                │ │
│ │                                                                         │ │
│ │ DIMENSION               SPEND      SHARE     POP CHANGE   REGIME        │ │
│ │ ─────────────────────────────────────────────────────────────────────── │ │
│ │ prod-api-cluster        ₹5.24L     36.9%     +18.7%       SPIKE         │ │
│ │ prod-worker-cluster     ₹2.81L     19.8%     -2.1%        STABLE        │ │
│ │ prod-gpu-training       ₹1.21L      8.5%     +52.0%       ELEVATED      │ │
│ │ prod-batch-processing   ₹0.54L      3.8%     +1.4%        NORMAL        │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4-Level Progressive Drill-Down Flow
* **Level 1 (Top Level)**: Spend grouped by cloud service (EC2, RDS, S3, EKS). Clicking a row drills to Level 2.
* **Level 2 (Account Level)**: Spend within the selected service across accounts (Production, Staging, Data Platform).
* **Level 3 (Workload / Tag Level)**: Spend within account grouped by workload cluster or environment tag.
* **Level 4 (Resource Intelligence)**: Direct transition to the individual resource deep-dive view.

---

## 5.3 Changes (`/changes`, alias `/anomalies`) — What Happened

Conceptually reframed from passive "anomalies" to proactive **"Changes"**:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ CHANGES                                                                     │
│ Material shifts detected in technology economics and utilization            │
│                                                                             │
│ 4 significant changes detected across 90-day baseline                        │
│ Filter: [All] [Cost Spikes] [Usage Changes] [Infrastructure Drift]          │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ PRODUCTION API COMPUTE                                       +38.24%   │ │
│ │ Unplanned Cost Surge                                         ₹1.42L net │ │
│ │                                                                         │ │
│ │ Observed Window: Aug 22 – Sep 20 (30 Days)                              │ │
│ │ Account: aws-prod-01 (112233445566) · ap-south-1                        │ │
│ │                                                                         │ │
│ │ Primary Driver Hypothesis:                                              │ │
│ │ Egress traffic expansion and auto-scaled compute instances.             │ │
│ │                                                                         │ │
│ │ Empirical Evidence:                                                     │ │
│ │ • Incurred daily spend rose from ₹2,650 to ₹3,663/day                   │ │
│ │ • Baseline Z-score: 3.42 (Severity: HIGH)                               │ │
│ │ • Telemetry coverage: 94%                                               │ │
│ │                                                                         │ │
│ │ [Investigate Root Cause →]                 OBSERVED · DERIVED · INFERRED │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5.4 Optimization Workspace (`/optimization`) — Addressable Opportunities

An engineering decision workspace replacing generic recommendation tables:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ OPTIMIZATION WORKSPACE                                                      │
│ Quantified Waste Elimination & Rightsizing Portfolio                        │
│                                                                             │
│ ADDRESSABLE OPPORTUNITY                                                     │
│ ₹4.60L / month  (₹55.20L annualized) · 7 Opportunities · 8 Recommendations  │
│                                                                             │
│ CATEGORY ALLOCATION                                                         │
│ Compute   ████████████████████████░░░░░░░░  ₹2.40L / mo (52.2%)             │
│ Storage   ███████░░░░░░░░░░░░░░░░░░░░░░░░░  ₹0.72L / mo (15.7%)             │
│ Database  ██████░░░░░░░░░░░░░░░░░░░░░░░░░░  ₹0.61L / mo (13.3%)             │
│ Network   ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  ₹0.41L / mo  (8.9%)             │
│ Other     ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  ₹0.46L / mo  (9.9%)             │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ PROD ANALYTICS WORKER POOL                                              │ │
│ │ Compute Rightsizing Opportunity                                         │ │
│ │                                                                         │ │
│ │ Current Specification            Recommended Specification              │ │
│ │ m5.4xlarge (16 vCPU, 64 GB)  →   m5.large (2 vCPU, 8 GB)                │ │
│ │                                                                         │ │
│ │ Current Cost:      ₹58,000 / mo                                         │ │
│ │ Estimated Savings: ₹42,800 / mo  (₹513,600 / yr)                        │ │
│ │                                                                         │ │
│ │ Operational Telemetry Evidence:                                         │ │
│ │ • CPU p95: 8.5% (Median: 4.1%)                                          │ │
│ │ • Memory p95: 25.0%                                                     │ │
│ │ • Sampling Coverage: 95% (Sufficient)                                   │ │
│ │                                                                         │ │
│ │ Risk: LOW · Reversibility: HIGH · Complexity: LOW                       │ │
│ │ Epistemic Classes: OBSERVED · DERIVED · PROJECTED                       │ │
│ │                                                                         │ │
│ │ [Review Case File →]                          [Simulate in Scenario →]  │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5.5 Recommendation Detail (`/optimization/:id`) — Engineering Case File

Designed like an in-depth incident report or engineering RFC:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ ← Back to Optimization                                                      │
│                                                                             │
│ CASE FILE: REC-001                                                          │
│ Rightsizing Proposal: prod-analytics-worker-01                              │
│                                                                             │
│ m5.4xlarge → m5.large                                                       │
│ Monthly Invoiced Cost: ₹58,000 → ₹15,200                                    │
│ Projected Savings:     ₹42,800 / month (₹513,600 / year)                    │
│                                                                             │
│ 01 EMPIRICAL EVIDENCE                                                       │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Metric             Measured Value    Window     Sufficiency   Source        │
│ CPU Utilization    p95: 8.5%         14 Days    95% (OK)      CloudWatch    │
│ Memory Pressure    p95: 25.0%        14 Days    92% (OK)      CloudWatch    │
│ Network I/O        Max 12 MB/s       14 Days    95% (OK)      CloudWatch    │
│ Financial Base     ₹1,933.33 / day   90 Days    Authoritative Cost Explorer │
│                                                                             │
│ 02 WHY ATLAS BELIEVES THIS                                                  │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Over 14 continuous days of observation (4,032 5-minute telemetry samples),  │
│ this instance never exceeded 11.2% CPU utilization. The observed telemetry  │
│ is consistent with evaluating a rightsizing change to m5.large, which       │
│ maintains substantial capacity headroom above peak workload demand.        │
│                                                                             │
│ 03 TRADE-OFF EVALUATION                                                     │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Financial Impact        ████████████████████  HIGH    (₹42,800/mo)          │
│ Operational Confidence  ██████████████████░░  STRONG  (95% sample coverage) │
│ Performance Risk        ████░░░░░░░░░░░░░░░░  LOW     (Headroom > 70%)      │
│ Reversibility           ████████████████████  HIGH    (Instance stop/modify)│
│ Implementation Effort   ████░░░░░░░░░░░░░░░░  LOW     (Single maintenance)  │
│                                                                             │
│ 04 IMPLEMENTATION CONSIDERATIONS & ARCHITECTURAL BOUNDARY                   │
│ ─────────────────────────────────────────────────────────────────────────── │
│ Atlas does not execute infrastructure changes (Read-Only Boundary Enforced).│
│                                                                             │
│ Suggested Implementation Approach:                                          │
│ • Review proposed configuration against application performance SLOs       │
│ • Validate workload compatibility in staging or non-production environment  │
│ • Author infrastructure-as-code change (Terraform / CloudFormation / Pulumi)│
│ • Apply through standard organizational deployment controls & peer review   │
│                                                                             │
│ Rollback Considerations:                                                    │
│ Revert instance specification in infrastructure code to previous type.      │
│ Storage state and volume attachments remain preserved across type changes.  │
│                                                                             │
│ [Create Scenario with this Change]               [Mark as Under Review]     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5.6 Resource Intelligence (`/resources/:id`) — Synthesis & Telemetry

Deep inspection page for any individual cloud resource:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ RESOURCE INTELLIGENCE                                                       │
│                                                                             │
│ AmazonEC2 Instance                                                          │
│ prod-analytics-worker-01 (i-03fa48b91c)                                     │
│ m5.4xlarge (16 vCPU, 64 GB RAM) · Production · ap-south-1 · ● Running       │
│                                                                             │
│ FINANCIAL POSITION                                                          │
│ Current Spend: ₹58,240 / month (+12.4% PoP) · 90-Day Cumulative: ₹1.62L    │
│                                                                             │
│ OPERATIONAL EVIDENCE TELEMETRY                                              │
│                                                                             │
│ CPU Utilization (%)              Coverage: 95% (4,032 samples)             │
│ p95: 8.5% │ Median: 4.1% │ Peak: 10.9%                                     │
│   ╭─────────╮                                                               │
│ ──╯         ╰────────────────────────────────────────────────────────────── │
│                                                                             │
│ Memory Utilization (%)           Coverage: 93% (3,940 samples)             │
│ p95: 25.0% │ Peak: 28.4%                                                    │
│ ──────────────────────────╭──────────────────────────────────────────────── │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ ATLAS ASSESSMENT                                                        │ │
│ │                                                                         │ │
│ │ Compute capacity is materially above observed workload demand.          │ │
│ │ Evidence Strength: HIGH (95% telemetry completeness)                    │ │
│ │                                                                         │ │
│ │ Diagnostic Findings:                                                    │ │
│ │ • Observed CPU p95 has remained under 10% for 14 consecutive days.      │ │
│ │ • Zero memory pressure detected; swap usage is 0%.                      │ │
│ │ • Hardware capacity headroom is 91.5%.                                  │ │
│ │ • Telemetry quality is verified (95% sampling completeness).            │ │
│ │                                                                         │ │
│ │ The available evidence supports evaluating rightsizing to m5.large.     │ │
│ │                                                                         │ │
│ │ [View Rightsizing Proposal REC-001]             [Ask Atlas about this]  │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5.7 Scenarios Simulation Workbench (`/scenarios`) — Architecture Sandbox

An engineering workbench for simulating structural changes before execution:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ SCENARIO SIMULATION WORKBENCH                                               │
│ Model architectural and purchasing changes before committing                │
│                                                                             │
│ ACTIVE SCENARIO: Aggressive Compute Rightsizing (5 Resources)                │
│                                                                             │
│ ┌──────────────────┬──────────────────┬──────────────────┬────────────────┐ │
│ │ ₹12.50L          │ →                │ ₹8.90L           │ ₹3.60L / mo    │ │
│ │ Baseline Cost    │                  │ Projected Cost   │ Net Savings    │ │
│ └──────────────────┴──────────────────┴──────────────────┴────────────────┘ │
│                                                                             │
│ SIMULATION TRADE-OFF MATRIX                                                 │
│ Financial Savings:   -₹3,60,000 / month (-28.8%)                            │
│ Performance Impact:  Headroom maintained > 65% on all modified nodes        │
│ Reliability Risk:    LOW (Cluster HA preserved; min replica constraint OK)  │
│ Complexity:          MODERATE (Staged maintenance rollout required)         │
│ Reversibility:       HIGH (Instant rollback to previous instance sizes)     │
│                                                                             │
│ PLANNED MODIFICATIONS (5 Resources)                                         │
│ RESOURCE                   CURRENT SPEC     PROPOSED SPEC    SAVINGS / MO   │
│ ─────────────────────────────────────────────────────────────────────────── │
│ prod-analytics-worker-01   m5.4xlarge       m5.large         ₹42,800        │
│ prod-analytics-worker-02   m5.4xlarge       m5.large         ₹42,800        │
│ prod-api-worker-01         c5.2xlarge       c5.large         ₹28,400        │
│ prod-api-worker-02         c5.2xlarge       c5.large         ₹28,400        │
│ stage-k8s-node-01          t3.xlarge        t3.medium        ₹14,200        │
│                                                                             │
│ [Export IaC Change Spec]                         [Save Scenario]            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5.8 Forecast (`/forecast`) — Historical vs Projected Trajectory

A rigorous forecasting interface that never conflates historical facts with future projections:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ TECHNOLOGY SPEND FORECAST                                                   │
│ Statistical Holt-Winters & Moving Average Projections                       │
│                                                                             │
│ Horizon: [30 Days] [60 Days] [90 Days]                                      │
│ Projected 30-Day Run Rate: ₹13.80L (+10.4%) · Confidence Band: ±6.5%        │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ SPEND TRAJECTORY & PROJECTION                                           │ │
│ │                                                                         │ │
│ │ ₹16L ┤                                          ╱ (Upper 95% Bound)     │ │
│ │      │                                      ───╱░ (Forecast Trajectory) │ │
│ │ ₹13L ┤                             ────────╱░░░                         │ │
│ │      │                    ────────╯        ╲ (Lower 95% Bound)          │ │
│ │ ₹10L ┤────────────────────╯                                             │ │
│ │      │                    │                                             │ │
│ │      └────────────────────┼──────────────────────────────────────────── │ │
│ │        Historical Spend   │  Projected Trajectory                       │ │
│ │        (Solid Line)       ▲  (Dashed Line with Confidence Envelope)     │ │
│ │                         TODAY                                           │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ Epistemic Guarantee:                                                        │
│ Historical spend is OBSERVED. Forward projection is PROJECTED.              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5.9 Integrations (`/integrations`) — Trust Boundary Control Room

A control room emphasizing the absolute read-only boundary:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ INTEGRATIONS & CLOUD TRUST BOUNDARY                                         │
│ Active Provider Connections & Synchronization Health                        │
│                                                                             │
│ AMAZON WEB SERVICES                                                         │
│ Status: ● Connected · 3 Accounts Configured · 58 Monitored Resources        │
│ Last Synchronized: 8 minutes ago (Duration: 3.4s)                           │
│                                                                             │
│ Subsystem Provenance                                                        │
│ • Cost Explorer Adapter:    ● Active (90D Aggregated + 14D Resource-Level)  │
│ • CloudWatch Telemetry:     ● Active (5-min Sampling · 94% Coverage)        │
│ • Resource Inventory Scan:  ● Synchronized (EC2, RDS, EBS, S3, EKS)         │
│                                                                             │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ ARCHITECTURAL TRUST BOUNDARY GUARANTEES                                 │ │
│ │                                                                         │ │
│ │ ✓ Absolute Read-Only Guarantee Enforced                                 │ │
│ │   Codebase contains ZERO mutating AWS SDK calls.                        │ │
│ │                                                                         │ │
│ │ ✓ Automated AST Safety Scanner Verified                                 │ │
│ │   Verified: test_aws_safety.py passed static analysis of all adapters.  │ │
│ │                                                                         │ │
│ │ ✓ Least-Privilege Ephemeral Authentication                              │ │
│ │   STS AssumeRole credentials held in transient memory (1-hour TTL).     │ │
│ │   No root or IAM user access keys stored in database.                   │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│ [Test Connections]                                   [Trigger Manual Sync]  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5.10 Ask Atlas Drawer — The Research Result Console

The conversational AI interface presents structured research findings rather than casual chat:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ ASK ATLAS CONSOLE                                                     [ ✕ ] │
│ Technology Economics Investigation                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ User Query:                                                                 │
│ "Why did EC2 spend increase this month and can we safely reduce it?"        │
├─────────────────────────────────────────────────────────────────────────────┤
│ ATLAS RESEARCH FINDING                                                      │
│                                                                             │
│ EC2 spend increased by ₹2.14L (+18.7%) over the baseline period,            │
│ primarily driven by compute usage expansion in the Production API cluster.  │
│                                                                             │
│ Telemetry analysis indicates that capacity can be safely reduced.           │
│ Over 14 days, the cluster maintained a CPU p95 of 11.2% with 94% telemetry │
│ coverage, demonstrating 88.8% capacity headroom.                            │
│                                                                             │
│ KEY QUANTIFIED CLAIMS                                                       │
│ [₹2.14L Incurred Delta] [18.7% PoP Growth] [38% Usage Growth] [11.2% CPU]   │
│                                                                             │
│ EVIDENCE CITATIONS                                                          │
│ • [AWS Cost Explorer · ce-agg-ec2-202609]                                   │
│ • [CloudWatch Telemetry · cw-i-03fa48-cpu]                                  │
│ • [Optimization Opportunity · REC-001]                                      │
│                                                                             │
│ EPISTEMIC EVALUATION                                                        │
│ Classification: OBSERVED · DERIVED · INFERRED · PROJECTED                   │
│ Verification:   ✓ VERIFIED (All numeric claims within ±1.0% tolerance)      │
│ Context Hash:   SHA-256: e8f14b...d091                                      │
│                                                                             │
│ [Open Investigation in Spend Explorer]         [Review Recommendation 001]  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 6. Signature Components Anatomy & Behavioral Rules

## 6.1 The Evidence Layer (`EvidenceLayer`)

A signature component visually breaking down claims into epistemic tiers:

```typescript
export interface EvidenceItem {
  epistemicClass: 'OBSERVED' | 'DERIVED' | 'INFERRED' | 'ASSUMED' | 'PROJECTED';
  source: string; // e.g. "AWS Cost Explorer", "CloudWatch", "Analytical Engine"
  statement: string;
  metricValue?: string;
  timestamp?: string;
}

export const EvidenceLayer: React.FC<{ items: EvidenceItem[] }> = ({ items }) => {
  return (
    <div className="rounded-lg border border-atlas-border bg-atlas-surface p-4 space-y-3">
      <h4 className="text-xs font-mono font-semibold uppercase text-atlas-muted tracking-wider">
        Authoritative Evidence Layer
      </h4>
      <div className="space-y-2">
        {items.map((item, idx) => (
          <div key={idx} className="flex items-start gap-3 text-xs">
            <EpistemicBadge classification={item.epistemicClass} />
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="text-atlas-text font-medium">{item.statement}</span>
                {item.metricValue && (
                  <span className="font-mono text-atlas-primary">{item.metricValue}</span>
                )}
              </div>
              <span className="text-[11px] text-atlas-muted font-mono">{item.source}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

## 6.2 Multi-Dimensional Trade-Off Bars (`TradeOffDimensionBar`)
Replaces opaque composite scores with 5 independent dimension bars:
1. **Financial Impact** (High / Moderate / Low)
2. **Operational Confidence** (Strong / Moderate / Low)
3. **Performance Risk** (Low / Moderate / High)
4. **Reversibility** (High / Partially Reversible / Irreversible)
5. **Implementation Effort** (Low / Moderate / High)

## 6.3 Epistemic Classification Badges (`EpistemicBadge`)
Restrained pill component rendering epistemic tiers with crisp typography and subtle background tints:
- `OBSERVED`: Neutral slate
- `DERIVED`: Navy with light blue text
- `INFERRED`: Dark amber with gold text
- `ASSUMED`: Deep purple with violet text
- `PROJECTED`: Outlined cyan

## 6.4 Interactive Evidence Citation Pills (`EvidenceCitationPill`)
Clickable pills (e.g. `[Cost Record #4819]`) that open an inspection popover or navigate directly to the underlying record.

## 6.5 Telemetry Quality & Sufficiency Callouts
When telemetry coverage is $< 70\%$, the UI renders an explicit **Insufficient Evidence** warning:
> *"Telemetry coverage is 42% (minimum required: 70%). Recommendation withheld to prevent ungrounded downsizing."*

## 6.6 Evidence-Grounded Empty States
Replaces generic "No data found" with explanations grounded in sufficiency and data quality.

## 6.7 Evidence Strength Semantic Contract
Atlas strictly distinguishes **Evidence Strength** from statistical probability or certainty:
- **`HIGH`**: Strong supporting empirical evidence with verified sufficiency ($\ge 70\%$ sample coverage over $\ge 14$ days).
- **`MEDIUM`**: Meaningful evidence with minor limitations (e.g. 7–13 days or intermittent sampling gaps).
- **`LOW`**: Limited or incomplete evidence; flags uncertainty and withholds definitive recommendations.

*Semantics Principle*: Evidence Strength indicates the empirical availability, duration, and completeness of observations. It is never presented as an opaque predictive probability score (e.g. "95% probability of success").

---

# 7. Micro-Interactions, Transitions & Chart Rules

* **Page Transitions**: Subdued 150ms opacity transition (`transition-opacity duration-150`).
* **Hover State**: Card border transitions from `#1E2638` to `#2E3B55` without transform scaling or jumping.
* **Loading States**: Pulsing structural skeletons matching the exact component layout (`Skeleton.tsx`), never generic center spinners.
* **Chart Crosshairs**: Snapping crosshair with monospace tooltip displaying date, value, delta, and epistemic source.
* **Status Updates**: Subtle 2px dot pulse (`animate-pulse`) for active connections and running sync jobs.

---

# 8. Responsive Viewport Adaptations (1440px to Mobile)

* **Desktop Workstation (1440px+)**: Full two-column Command Center, persistent 64-width navigation sidebar, expanded data tables.
* **Compact Desktop (1280px)**: Sidebar narrows, data cards wrap into two equal columns.
* **Tablet (1024px)**: Sidebar collapses into an icon-only rail; table columns hide secondary telemetry metrics.
* **Mobile (< 768px)**: Executive Inspection Mode:
  - Top bar narrows to logo and status.
  - Command Center presents high-level KPIs, recent significant changes, and instant Ask Atlas inquiry.
  - Deep multi-column data tables collapse into expandable summary cards.

---

# 9. Step-by-Step Implementation Blueprint for Antigravity

To execute this specification cleanly without disrupting existing backend APIs or test suites, Antigravity will proceed in structured execution steps:

### Step 1: Design System & Shared Token Updates
- Update `packages/design-system/index.ts` and `apps/web/tailwind.config.ts` with new color tokens, font rules, and epistemic badge classes.
- Verify that `JetBrains Mono` and `Inter` font configurations are properly applied.

### Step 2: Global Chrome & Navigation Shell
- Refactor `apps/web/src/components/Sidebar.tsx` to reflect the new 5-tier navigation hierarchy (`OVERVIEW`, `FINANCIAL`, `INTELLIGENCE`, `INFRASTRUCTURE`, `SYSTEM`).
- Refactor `apps/web/src/components/Topbar.tsx` into the comprehensive **System Context Bar** with organization selector, currency/time scope, and trust flyout modal.
- Create `apps/web/src/components/ai/AskAtlasDrawer.tsx` to provide global conversational inquiry from any screen.
- Wire `AppShell.tsx` to house the drawer and persistent context states.

### Step 3: Signature Components Creation
- Create `apps/web/src/components/ui/EvidenceLayer.tsx`.
- Create `apps/web/src/components/ui/TradeOffDimensionBar.tsx`.
- Refactor `EpistemicBadge.tsx` and `EvidenceCitationPill.tsx`.

### Step 4: Command Center (`/dashboard`) Transformation
- Overhaul `apps/web/src/pages/DashboardPage.tsx` into the **Technology Financial Intelligence Command Center**.
- Integrate Spend Trajectory chart with plotted anomaly pins, "What Changed?" primary driver card, Top Cost Drivers list, and Needs Attention queue.

### Step 5: Spend Explorer (`/spend`) & Progressive Drill-Down
- Overhaul `apps/web/src/pages/SpendPage.tsx` with view toggles (Spend, Δ, %, 7D/14D/30D), dimensional grouping, and 4-level progressive drill-down.

### Step 6: Changes (`/changes`), Optimization (`/optimization`), & Recommendation Detail
- Add route `/changes` aliasing `/anomalies` with the new "Changes" visual language.
- Update `OptimizationPage.tsx` into the quantified opportunity decision workspace.
- Enhance `RecommendationDetailPage.tsx` into the engineering case file format with independent trade-off bars.

### Step 7: Resource Intelligence (`/resources/:id`) & Scenarios Workbench (`/scenarios`)
- Update `ResourceDetailPage.tsx` with telemetry sparklines, coverage indicators, and the Atlas Assessment card.
- Refactor `ScenariosPage.tsx` into the simulation workbench.

### Step 8: Integrations (`/integrations`), Forecast (`/forecast`), & Polish
- Update `IntegrationsPage.tsx` with trust boundary verification cards and AST safety proof.
- Update `ForecastPage.tsx` with explicit historical vs projected visual demarcation.
- Verify end-to-end frontend tests and production Vite build.
