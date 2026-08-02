from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server-side configuration. Secrets must never be serialized to clients or logs."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    nvidia_api_key: str = Field(default="", repr=False)
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"

    max_parallel_agents: int = Field(default=2, ge=1, le=16)
    max_agent_calls: int = Field(default=20, ge=1)
    max_agent_retries: int = Field(default=2, ge=0, le=10)
    max_repair_cycles: int = Field(default=3, ge=0, le=10)
    request_timeout_seconds: float = Field(default=120, gt=0, le=600)


@lru_cache
def get_settings() -> Settings:
    return Settings()
