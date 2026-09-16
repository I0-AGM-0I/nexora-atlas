"""
NEXORA ATLAS - Application Entrypoint
FastAPI modular monolith backend.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
setup_exception_handlers(app)

# Mount all application routers
app.include_router(root_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
