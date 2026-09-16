# ADR 001: Modular Monolith Architecture

## Status
Accepted

## Context
NEXORA ATLAS requires high cohesion between domain intelligence engines (spend aggregation, anomaly detection, waste rules, forecasting, scenario simulations) and the core relational data model. Introducing microservices prematurely would incur significant network overhead, distributed transaction complexity, deployment fragility, and unnecessary DevOps friction.

## Decision
We build NEXORA ATLAS as a single **modular monolith**:
- A single FastAPI backend application with domain boundaries partitioned into explicit modules (`apps/api/app/engines/`).
- Shared transactional database access managed through SQLAlchemy 2.0.
- A single frontend SPA (`apps/web`).

## Consequences
- **Positive**: Simplified local development, instantaneous type synchronization, zero distributed latency between engines, single-command startup.
- **Negative**: Requires discipline to enforce module boundaries and prevent spaghetti imports across engines.
