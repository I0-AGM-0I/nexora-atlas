# NEXORA ATLAS

> **Technology Cost Intelligence & Optimization Platform**
> *"Know where technology money is going — and what to do about it."*

NEXORA ATLAS transforms raw cloud technology spend into actionable cost intelligence, explainable waste detection, statistical anomaly attribution, forward-looking forecasting, and strategic scenario simulations.

---

## Architecture Overview

ATLAS is constructed as a modern, high-performance **modular monolith**:

- **Backend**: Python 3.12+ / FastAPI / SQLAlchemy 2.0 / Pydantic v2 / Alembic
- **Frontend**: React 18+ / TypeScript / Vite / Tailwind CSS / Lucide React
- **Canonical Database**: PostgreSQL 16 (production & containerized)
- **Local Fallback Database**: SQLite (`aiosqlite`) for zero-dependency local development
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

# Start Vite dev server (runs on http://localhost:5173)
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## Running with Docker Compose (PostgreSQL Production Target)

When Docker is available:

```bash
# Start PostgreSQL 16
docker-compose up -d postgres

# Or start the entire stack (PostgreSQL + FastAPI + Vite)
docker-compose up --build
```

---

## Testing

### Backend Tests (pytest)
```bash
cd apps/api
pytest tests -v
```

### Frontend Tests (Vitest & TypeScript)
```bash
cd apps/web
npm test
npm run build
```

---

## Key Endpoints
- `GET /health` - System health and database connection status
- `GET /api/v1/meta` - Service identity, API version, and demo mode flag
- `GET /docs` - Interactive OpenAPI documentation

---

## Documentation
- [System Architecture](docs/architecture/system.md)
- [Data Model](docs/architecture/data-model.md)
- [Telemetry Separation](docs/architecture/telemetry-separation.md)
- [AWS Integration](docs/architecture/aws-integration.md)
- [ADR 001: Modular Monolith](docs/decisions/001-modular-monolith.md)
- [ADR 002: Dual Database Strategy](docs/decisions/002-dual-database-strategy.md)
