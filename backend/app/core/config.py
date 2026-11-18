"""Application configuration settings."""
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, RedisDsn


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = Field(..., min_length=32)
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://devpilot:devpilot@localhost:5432/devpilot"
    )
    POSTGRES_USER: str = "devpilot"
    POSTGRES_PASSWORD: str = "devpilot"
    POSTGRES_DB: str = "devpilot"

    # Redis
    REDIS_URL: RedisDsn = Field(default="redis://localhost:6379/0")

    # GitHub App
    GITHUB_APP_ID: Optional[int] = None
    GITHUB_APP_PRIVATE_KEY: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None

    # GitHub OAuth
    GITHUB_OAUTH_CLIENT_ID: Optional[str] = None
    GITHUB_OAUTH_CLIENT_SECRET: Optional[str] = None

    # Claude API
    ANTHROPIC_API_KEY: Optional[str] = None
    CLAUDE_MODEL: str = "claude-fable-5-2"

    # Execution
    DOCKER_HOST: str = "unix:///var/run/docker.sock"
    EXECUTION_TIMEOUT: int = 300
    MAX_CONCURRENT_EXECUTIONS: int = 5

    # Frontend
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000"
    NEXT_PUBLIC_WS_URL: str = "ws://localhost:8000"

    # Observability
    SENTRY_DSN: Optional[str] = None

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()