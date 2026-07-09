from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    environment: str = "local"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "sqlite:////app/data/sqlite/berrybrain.db"
    vault_path: Path = Path("/app/vault")
    jobs_path: Path = Path("/app/data/jobs")
    log_path: Path = Path("/app/data/logs")
    vault_watcher_enabled: bool = True
    vault_watcher_interval_seconds: int = 10
    api_token: str = ""
    cors_origins: str = "*"
    backup_path: Path = Path("/app/data/backups")

    model_config = SettingsConfigDict(
        env_prefix="BERRYBRAIN_",
        env_file=PROJECT_ROOT / ".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
