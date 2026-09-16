# ADR 002: Dual Database Compatibility Strategy

## Status
Accepted

## Context
NEXORA ATLAS requires PostgreSQL 16 as its authoritative enterprise database engine for production deployments and Docker Compose workflows. However, developers or CI runners may operate on environments where Docker or a local PostgreSQL service is temporarily unavailable. 

## Decision
We implement a dual-engine abstraction through SQLAlchemy 2.0 and Alembic:
1. **Canonical Production Target**: PostgreSQL 16 (configured in `docker-compose.yml`, `infra/postgres`, and `.env.example`).
2. **Local Zero-Docker Fallback**: SQLite (with `aiosqlite` for asynchronous operations) enabled automatically via `DATABASE_URL=sqlite+aiosqlite:///./atlas_dev.db`.
3. **Portability Guardrails**: Domain models avoid database-specific proprietary features (e.g. native PostgreSQL enums or SQLite-specific triggers). Standard ANSI SQL, portable string UUIDs, and generic JSON columns are enforced.

## Consequences
- **Positive**: Zero developer onboarding friction; works instantly on any machine without installing Docker Desktop or PostgreSQL; identical domain models used in both contexts.
- **Negative**: Developers must maintain strict discipline to avoid vendor-locked raw SQL queries in domain code.
