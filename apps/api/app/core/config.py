from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "StrideCoach API"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    database_url: str = (
        "postgresql+psycopg://postgres:YOUR_DATABASE_PASSWORD"
        "@db.YOUR_PROJECT_REF.supabase.co:5432/postgres"
    )
    backend_cors_origins: str = Field(default="http://localhost:5173")
    frontend_app_url: str = "http://localhost:5173"
    supabase_url: AnyHttpUrl | None = None
    supabase_jwt_secret: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"
    strava_client_id: str | None = None
    strava_client_secret: str | None = None
    strava_redirect_uri: str = "http://localhost:8000/api/v1/strava/callback"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
