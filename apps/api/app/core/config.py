"""
NEXORA ATLAS - Application Configuration
Uses pydantic-settings to validate environment variables with secure defaults.
"""

from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Service Identity
    SERVICE_NAME: str = "nexora-atlas-api"
    API_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Operational Mode
    DEMO_MODE: bool = True

    # Database Configuration
    # Canonical Production: postgresql+asyncpg://user:pass@host:5432/db
    # Local Development / Zero-Docker Fallback: sqlite+aiosqlite:///./atlas_dev.db
    DATABASE_URL: str = "sqlite+aiosqlite:///./atlas_dev.db"

    # CORS Configuration
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # AWS Ingestion Credentials (Optional in Phase 1 / Demo Mode)
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_SESSION_TOKEN: str = ""
    AWS_ROLE_ARN: str = ""

    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.DATABASE_URL.lower()

    @property
    def is_postgres(self) -> bool:
        return "postgres" in self.DATABASE_URL.lower()


# Singleton settings instance
settings = Settings()
