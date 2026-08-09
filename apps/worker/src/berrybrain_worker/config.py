from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[4]


class WorkerSettings(BaseSettings):
    api_url: str = "http://localhost:8000"
    api_token: str = ""
    ollama_base_url: str = ""
    main_model: str = ""
    fast_model: str = ""
    embedding_model: str = ""
    reasoning_model: str = ""
    loop_interval_seconds: int = 5
    max_consecutive_empty: int = 30
    max_concurrent_jobs: int = 4
    cloud_max_concurrent_jobs: int = 1
    ollama_timeout: int = 120
    hipporag_url: str = "http://localhost:8000"
    hipporag_service_token: str = ""

    model_config = SettingsConfigDict(
        env_prefix="BERRYBRAIN_",
        env_file=PROJECT_ROOT / ".env",
        extra="ignore",
    )
