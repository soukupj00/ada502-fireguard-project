from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Manages application settings and configurations."""

    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/fireguard"
    REDIS_URL: str = "redis://redis:6379/0"
    FETCH_INTERVAL_SECONDS: int = 3600  # 3600
    MAX_CONCURRENT_FETCHES: int = 5

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None) -> str:
        if v and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://")
        return v or "postgresql+asyncpg://user:password@localhost/fireguard"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
