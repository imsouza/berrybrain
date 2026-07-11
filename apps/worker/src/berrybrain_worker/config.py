from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[4]


class WorkerSettings(BaseSettings):
    api_url: str = "http://localhost:8000"
    api_token: str = ""
    ollama_base_url: str = "http://localhost:11434"
    main_model: str = "qwen3:8b"
    fast_model: str = "gemma3:4b"
    embedding_model: str = "bge-m3"
    reasoning_model: str = "deepseek-r1:8b"
    loop_interval_seconds: int = 5
    max_consecutive_empty: int = 30
    ollama_timeout: int = 120

    model_config = SettingsConfigDict(
        env_prefix="BERRYBRAIN_",
        env_file=PROJECT_ROOT / ".env",
        extra="ignore",
    )
