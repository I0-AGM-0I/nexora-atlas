"""
NEXORA ATLAS - Application Configuration
Uses pydantic-settings to validate environment variables with secure defaults.
"""

from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_SQLITE_PATH = (BASE_DIR / "atlas_dev.db").as_posix()


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
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DEFAULT_SQLITE_PATH}"

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def assemble_database_url(cls, v: str) -> str:
        if v.startswith("sqlite+aiosqlite:///./") or v.startswith("sqlite:///./"):
            relative_part = v.split(":///./", 1)[1]
            abs_path = (BASE_DIR / relative_part).as_posix()
            return f"sqlite+aiosqlite:///{abs_path}"
        return v

    # CORS Configuration
    CORS_ORIGINS: Union[str, List[str]] = (
        "http://localhost:5173,http://localhost:5174,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:5174"
    )

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

    # AI Explanation & Natural Language Intelligence (Phase 9)
    AI_ENABLED: bool = False
    AI_PROVIDER: str = "mock"  # "mock" or "openai"
    AI_API_KEY: str = ""
    AI_MODEL: str = "gpt-4o-mini"
    AI_MAX_CONTEXT_TOKENS: int = 8000
    AI_MAX_OUTPUT_TOKENS: int = 1500
    AI_TIMEOUT_SECONDS: int = 30
    MAX_AI_REQUESTS_PER_MINUTE: int = 20
    MAX_AI_REQUESTS_PER_ORGANIZATION: int = 100
    MAX_AI_RETRIES: int = 1
    MAX_PERSISTED_EVIDENCE_BYTES: int = 32768
    MAX_SESSION_MESSAGES: int = 10
    MAX_SESSION_CONTEXT_TOKENS: int = 2000
    SESSION_RETENTION_HOURS: int = 24

    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.DATABASE_URL.lower()

    @property
    def is_postgres(self) -> bool:
        return "postgres" in self.DATABASE_URL.lower()


# Singleton settings instance
settings = Settings()
