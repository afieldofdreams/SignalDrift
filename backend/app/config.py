from pathlib import Path

from pydantic_settings import BaseSettings

# Resolve the root .env relative to this file: backend/app/config.py -> ../../.env
_ROOT_ENV = Path(__file__).resolve().parent.parent.parent / ".env"


_BACKEND_DIR = Path(__file__).resolve().parent.parent

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".csv", ".xlsx", ".xls", ".md", ".rtf"}


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    log_level: str = "info"
    upload_dir: str = "uploads"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    db_path: str = "signaldrift.db"

    @property
    def upload_path(self) -> Path:
        """Resolve upload directory. Absolute paths used as-is, relative resolved from backend root."""
        p = Path(self.upload_dir)
        return p if p.is_absolute() else _BACKEND_DIR / p

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    model_config = {
        "env_file": str(_ROOT_ENV),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
