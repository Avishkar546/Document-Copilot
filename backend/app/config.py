from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    database_url: str
    app_database_url: str

    # Comma-separated in .env; use `cors_origins` for the parsed list.
    allowed_origins: str = "http://localhost:5173"

    @computed_field
    @property
    def sqlalchemy_database_url(self) -> str:
        """Normalize the migration URL for SQLAlchemy + psycopg v3."""
        return self._normalize_postgres_url(self.database_url)

    @computed_field
    @property
    def sqlalchemy_app_database_url(self) -> str:
        """Normalize the least-privilege application URL for psycopg v3."""
        if self.app_database_url is None:
            raise ValueError(
                "APP_DATABASE_URL must be set before the app can access the database"
            )
        return self._normalize_postgres_url(self.app_database_url)

    @staticmethod
    def _normalize_postgres_url(url: str) -> str:
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg://", 1)
        return url

    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]


settings = Settings()
