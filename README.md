# NEXORA ATLAS — Technology Financial Intelligence Command Center

[![NEXORA ATLAS CI/CD Pipeline](https://github.com/I0-AGM-0I/nexora-atlas/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/I0-AGM-0I/nexora-atlas/actions/workflows/ci-cd.yml)

> **Technology Cost Intelligence & Optimization Platform**
> *"Know where technology money is going — and what to do about it."*

NEXORA ATLAS transforms raw cloud technology spend into actionable cost intelligence, explainable waste detection, statistical anomaly attribution, forward-looking forecasting, and strategic scenario simulations.

- **Live Production Deployment**: [https://nexora-atlas.onrender.com/dashboard](https://nexora-atlas.onrender.com/dashboard)
- **GitHub Repository**: [https://github.com/I0-AGM-0I/nexora-atlas](https://github.com/I0-AGM-0I/nexora-atlas)
- **Current Production Verification**: Commit `9bec34e` (Live application footer displays `Commit: 9bec34e`)

---

> 📖 **Comprehensive System Documentation**: For an exhaustive, file-by-file, mathematical, and architectural deep-dive of the entire system from A to Z, see [SYSTEM_DOCUMENTATION.md](file:///d:/Nexora%20Atlas/SYSTEM_DOCUMENTATION.md).

---

## Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend API** | Python 3.12, FastAPI (modular monolith), Pydantic v2, Uvicorn |
| **Database & ORM** | PostgreSQL 16 (canonical production), SQLite / `aiosqlite` (local fallback), SQLAlchemy 2.0 (async), Alembic |
| **Frontend SPA** | React 19, TypeScript, Vite, Tailwind CSS, Lucide React |
| **Containerization** | Docker (multi-stage production container compiling React & running FastAPI) |
| **CI/CD Pipeline** | GitHub Actions (gated 4-stage pipeline) |
| **Cloud Hosting** | Render (Web Service with automated deploy webhook) |

---

## Architecture Overview

ATLAS is constructed as a modern, high-performance **modular monolith**:

- **Unified Production Container**: A multi-stage Docker build where Stage 1 builds the React 19 SPA with Vite, and Stage 2 runs the Python 3.12 FastAPI backend which serves both the REST API (`/api/v1/*`) and the compiled static SPA with client-side routing fallback.
- **Dynamic Port Binding**: Conforms to dynamic cloud environments via Render's dynamic `$PORT` environment variable.
- **Idempotent Data Engine**: Automatically bootstraps and deterministically seeds baseline estate data on container startup without destroying existing state.
- **Design Language**: Enterprise FinOps dark theme (`#080B10`), monospace tabular figures, Bloomberg/Datadog-grade information density.

---

## Quick Start (Local Development without Docker)

ATLAS supports a zero-friction development mode using SQLite fallback:

### 1. Backend Setup
```bash
# Navigate to API app
cd apps/api

# Create virtual environment & install dependencies
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run backend API server (runs on http://localhost:8000)
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
# Navigate to Web app
cd apps/web

# Install dependencies
npm install

# Start Vite dev server (runs on http://localhost:5173, opens automatically in browser)
npm run dev
```

The browser will automatically open to `http://localhost:5173`.

> 💡 **One-Command Quick Start (Windows)**:
> Run `.\run-all.bat` or `.\run-all.ps1` from the root directory to launch both the backend API and frontend dev server and automatically open the application in your browser.

---

## Running with Docker (Production Target)

### Single Unified Production Container
```bash
# Build the unified production container (injecting Git commit SHA)
docker build -t nexora-atlas:local .

# Run container locally bound to port 8000
docker run -p 8000:8000 nexora-atlas:local
```

### Multi-Container Stack (with PostgreSQL)
```bash
# Start PostgreSQL 16
docker-compose up -d postgres

# Or start the entire stack
docker-compose up --build
```

---

## Testing & Quality Assurance

### Backend Automated Tests (Pytest)
```bash
cd apps/api
pytest tests -v
# Or run with quiet summary:
python -m pytest apps/api -q
```
*Current test suite: **283 / 283 passed**, including dedicated CCA submission verification tests.*

### Frontend Automated Tests (Vitest)
```bash
cd apps/web
npm test -- --run
```
*Current test suite: **62 / 62 passed** across 10 test suites.*

### Code Quality & Static Analysis (Linting)
```bash
# Backend linting (Ruff)
ruff check apps/api

# Frontend linting (ESLint)
cd apps/web
npm run lint
```

---

## CI/CD Pipeline & Deployment Architecture

The automated delivery pipeline is configured in [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) with **strict sequential gating**:

```
Stage 1: Lint & Static Analysis (Ruff + ESLint)
  ↓ (requires Stage 1 pass)
Stage 2: Automated Unit & Integration Tests (283 Pytest + 62 Vitest)
  ↓ (requires Stage 1 + Stage 2 pass)
Stage 3: Docker Image Build Validation (Vite compilation + smoke test)
  ↓ (requires Stage 3 pass, master push only)
Stage 4: Production Deployment (Render Deploy Webhook)
```

### Strict Deployment Gating
* **Production Deployment** is strictly gated behind successful completion of all preceding stages (`lint`, `test`, and `docker-build`).
* **Auto-Deploy on Render is Disabled**: Render does not poll or automatically deploy repository pushes. Deployments can only be triggered when GitHub Actions dispatches an authenticated HTTP POST to `RENDER_DEPLOY_HOOK_URL` in Stage 4.

### Deliberate Failure & Recovery Demonstration
As required by the CCA 2 specification, the deployment gate's defensive integrity was empirically demonstrated:
1. **Deliberate Failure (Run #7, commit `5e9845a`)**: An assertion in `test_cca_requirement_health_endpoint` was intentionally changed to expect `status == "degraded"`.
   * **Result**: Stage 1 (Lint) passed, Stage 2 (Tests) failed, and both Stage 3 (Docker Build) and Stage 4 (Production Deployment) were **immediately blocked and skipped**. The live production application remained online and completely unaffected.
2. **Recovery Deployment (Run #8, commit `9bec34e`)**: The health check assertion was restored to `status == "healthy"`.
   * **Result**: All 4 stages succeeded, triggering the Render deployment webhook and deploying commit `9bec34e` to production.

---

## Key Endpoints

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/health` | `GET` | System operational health, database connectivity status, and service identification |
| `/api/v1/integrations/aws/configure` | `POST` | Dynamic AWS integration configuration with strict Pydantic payload validation and database state mutation |
| `/api/v1/meta` | `GET` | Service identity, API version, and operational mode |
| `/api/v1/demo/status` | `GET` | Demo estate health and financial reconciliation report |
| `/docs` | `GET` | Interactive Swagger / OpenAPI documentation |

---

## Demo Data Engine (Offline Synthetic Environment)

ATLAS includes a deterministic, offline-safe **Demo Data Engine** generating a cohesive synthetic cloud organization (**Nexora Labs Inc**) across 3 AWS accounts, 58 resources, 90 days of daily cost history (5,220 cost records), 4 explainable anomalies, 7 optimization opportunities, 8 actionable recommendations, 3 forecast horizons, and 3 strategic scenarios.

### Seeding via CLI
```bash
python scripts/seed_demo.py
```

### Demo Management Endpoints
When `DEMO_MODE=true` (default in development), the following endpoints are available:
- `GET /api/v1/demo/status` - Returns dataset health metrics, resource counts, and financial reconciliation status.
- `POST /api/v1/demo/seed` - Triggers deterministic demo dataset seed (with automated reset first).
- `POST /api/v1/demo/reset` - Safely purges demo records (`is_demo=True`) while preserving real production tenants.

When `DEMO_MODE=false`, these endpoints return `403 Forbidden`.

---

## Documentation

- [System Architecture](docs/architecture/system.md)
- [Data Model](docs/architecture/data-model.md)
- [Demo Data Engine](docs/architecture/demo-data-engine.md)
- [Telemetry Separation](docs/architecture/telemetry-separation.md)
- [AWS Integration](docs/architecture/aws-integration.md)
- [ADR 001: Modular Monolith](docs/decisions/001-modular-monolith.md)
- [ADR 002: Dual Database Strategy](docs/decisions/002-dual-database-strategy.md)
