"""
NEXORA ATLAS - Application Entrypoint
FastAPI modular monolith backend.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.api.router import root_router
from app.core.config import settings
from app.core.errors import setup_exception_handlers
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle hooks: initialize connections on startup, clean up on shutdown."""
    logger.info(
        f"Starting {settings.SERVICE_NAME} v{settings.API_VERSION} in {settings.ENVIRONMENT} mode "
        f"(Demo Mode: {settings.DEMO_MODE}, Database: {'SQLite' if settings.is_sqlite else 'PostgreSQL'})"
    )
    yield
    logger.info(f"Shutting down {settings.SERVICE_NAME}.")


app = FastAPI(
    title="NEXORA ATLAS API",
    description="Technology Cost Intelligence & Optimization Platform API",
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
setup_exception_handlers(app)

# Mount all application routers
app.include_router(root_router)

# Production static SPA serving (only active if static files exist)
static_dir = os.environ.get("STATIC_DIR")
if not static_dir:
    potential_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "apps", "web", "dist")
    )
    if not os.path.isdir(potential_path):
        potential_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "web", "dist")
        )
    if os.path.isdir(potential_path):
        static_dir = potential_path

if static_dir and os.path.isdir(static_dir):
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Strict API isolation: any /api/* route that reaches here is an unknown API endpoint
        if full_path.startswith("api/") or full_path == "api":
            raise HTTPException(status_code=404, detail=f"API route '/{full_path}' not found")

        # Static file check (e.g. vite.svg, favicon.ico, etc.)
        candidate_file = os.path.join(static_dir, full_path)
        if full_path and os.path.isfile(candidate_file):
            return FileResponse(candidate_file)

        # SPA BrowserRouter fallback: serve index.html
        index_file = os.path.join(static_dir, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)

        raise HTTPException(status_code=404, detail="SPA index.html not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
