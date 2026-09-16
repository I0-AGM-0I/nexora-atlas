# System Architecture - NEXORA ATLAS

NEXORA ATLAS is an enterprise-grade technology cost intelligence and optimization platform designed for engineering leaders, FinOps practitioners, and infrastructure architects.

## 1. High-Level Architecture

ATLAS is structured as a **modular monolith** with clean layer boundaries:

```
[ React 18+ SPA (TypeScript + Tailwind CSS + Lucide) ]
                      │
              HTTPS / JSON REST
                      │
                      ▼
        [ FastAPI Backend Layer ]
    ├── API Routers (/api/v1/*, /health)
    ├── Application Services
    ├── Domain Intelligence Engines
    │   ├── Spend Intelligence Engine
    │   ├── Anomaly Detection Engine
    │   ├── Waste Detection Engine
    │   ├── Recommendation Engine
    │   ├── Forecast Engine
    │   └── Scenario Simulation Engine
    ├── Cloud Provider Abstraction (AWSProvider -> CloudProvider)
    ├── Repositories (Data Access Layer)
    └── Persistence (SQLAlchemy 2.0 ORM)
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
   [ PostgreSQL 16 ]        [ SQLite Fallback ]
  Canonical Production      Local / Zero-Docker
  & Docker Compose          Development & CI
```

## 2. Layer Responsibilities

### Frontend Layer (`apps/web`)
- Single-page application built with Vite, React, TypeScript, and Tailwind CSS.
- High-density FinOps design language utilizing dark backgrounds (`#080B10`), monospace tabular figures, and restrained alert colors.
- Communicates with backend strictly via typed API clients matching backend Pydantic schemas.

### API Layer (`apps/api/app/api`)
- FastAPI routers grouped under `/api/v1/`.
- Handles request validation, dependency injection (database sessions, authentication context), and HTTP status codes.
- Does not contain business logic or direct ORM manipulations.

### Services Layer (`apps/api/app/services`)
- Orchestrates multi-step business transactions, coordinating between providers, repositories, and domain engines.

### Domain Intelligence Engines (`apps/api/app/engines`)
- Pure domain logic isolated from external APIs and databases.
- Evaluates cost aggregations, deterministic statistical anomaly detection, waste rule sets, right-sizing calculations, and scenario modeling.

### Cloud Provider Layer (`apps/api/app/integrations`)
- Isolates cloud-specific SDKs (e.g. AWS `boto3`) behind generic interfaces (`CloudProvider`).
- Implements resilient error handling, retries, pagination, and data normalization.

### Persistence Layer (`apps/api/app/models`, `apps/api/app/repositories`)
- SQLAlchemy 2.0 declarative models with strict type annotations.
- Generic repository patterns isolating database operations.
- Compatible with PostgreSQL (production) and SQLite (local zero-Docker developer fallback).
