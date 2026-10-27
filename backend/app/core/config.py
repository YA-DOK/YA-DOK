
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_env: str = "development"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_jwt_secret: str = ""

    # Database
    database_url: str = ""
    migration_database_url: str = ""

    # AI
    llm_provider: str = "openrouter"
    openrouter_api_key: str = ""
    llm_model: str = ""

    # Redis
    redis_url: str = ""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        extra="ignore",
    )


settings = Settings()
