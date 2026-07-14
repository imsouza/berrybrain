import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _discover_project_root() -> Path:
    configured = os.getenv("BERRYBRAIN_PROJECT_ROOT", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()

    module_path = Path(__file__).resolve()
    for candidate in module_path.parents:
        if (candidate / "docker-compose.yml").is_file() and (
            candidate / "apps"
        ).is_dir():
            return candidate
    return Path.cwd().resolve()


PROJECT_ROOT = _discover_project_root()


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
    allowed_hosts: str = "localhost,127.0.0.1,testserver,optlabs.com.br"
    max_request_body_bytes: int = 25 * 1024 * 1024
    trust_x_forwarded_for: bool = False
    cors_origins: str = "http://localhost:3000"
    backup_path: Path = Path("/app/data/backups")
    searxng_url: str = "http://localhost:8888"
    public_app_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    session_secret: str = "dev-change-me"
    session_cookie_name: str = "bb_session"
    session_secure_cookie: bool = False
    csrf_cookie_name: str = "bb_csrf"
    require_auth: bool = True
    donation_url: str = ""
    auth_rate_limit_window_seconds: int = 900
    auth_rate_limit_max_attempts: int = 8
    auth_lockout_minutes: int = 15
    auth_otp_ttl_minutes: int = 10
    auth_otp_resend_cooldown_seconds: int = 60
    admin_email: str = "admin@local.berrybrain"
    owner_username: str = "admin"
    attachment_ocr_executable: str = "tesseract"
    attachment_ocr_language: str = "eng"
    attachment_transcription_executable: str = "faster-whisper"
    attachment_transcription_model: str = (
        "/opt/berrybrain/models/faster-whisper-tiny.en"
    )
    attachment_extractor_timeout_seconds: int = 300

    smtp_host: str = Field(default="", validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=587, validation_alias="SMTP_PORT")
    smtp_user: str = Field(default="", validation_alias="SMTP_USER")
    smtp_password: str = Field(default="", validation_alias="SMTP_PASSWORD")
    smtp_from: str = Field(
        default="contato@optlabs.com.br", validation_alias="SMTP_FROM"
    )

    model_config = SettingsConfigDict(
        env_prefix="BERRYBRAIN_",
        env_file=PROJECT_ROOT / ".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
