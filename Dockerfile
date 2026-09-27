# ==============================================================================
# NEXORA ATLAS - Unified Multi-Stage Production Container
# Builds React 19 Frontend -> Mounts into FastAPI Asynchronous Backend
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Frontend Build Tier (Node.js 20)
# ------------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /app/web

# Pass running commit SHA into Vite build-time environment (GitHub Actions or Render)
ARG RENDER_GIT_COMMIT=""
ARG VITE_COMMIT_SHA=${RENDER_GIT_COMMIT}
ENV VITE_COMMIT_SHA=${VITE_COMMIT_SHA:-dev}
ENV RENDER_GIT_COMMIT=${RENDER_GIT_COMMIT}

# Install dependencies with lockfile consistency
COPY apps/web/package*.json ./
RUN npm ci

# Copy web source and shared design packages
COPY apps/web/ ./
COPY packages/ /app/packages/

# Execute production Vite build
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Monolith Runtime Tier (Python 3.12)
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS runtime
WORKDIR /app

# Install system utilities (curl for container healthcheck & smoke testing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install backend dependencies
COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend code, shared packages, and operational scripts
COPY apps/api /app/apps/api
COPY packages /app/packages
COPY scripts /app/scripts

# Copy compiled static frontend distribution from Stage 1
COPY --from=frontend-builder /app/web/dist /app/apps/web/dist

# Create persistent data directory
RUN mkdir -p /app/data

# Configure runtime execution environment
WORKDIR /app/apps/api
ENV PYTHONPATH="/app/apps/api:/app"
ENV STATIC_DIR="/app/apps/web/dist"
ENV DEMO_MODE="true"
ENV ENVIRONMENT="production"
ENV DATABASE_URL="sqlite+aiosqlite:////app/data/atlas_prod.db"
ENV PORT=8000

EXPOSE 8000

# Container entrypoint:
# 1. Non-destructively initializes/seeds database if uninitialized
# 2. Starts Uvicorn server bound to dynamic Render $PORT
CMD ["sh", "-c", "python /app/scripts/seed_demo.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

