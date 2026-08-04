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
    nvidia_default_model: str = "openai/gpt-oss-120b"

    # Persist learned model health/latency across application restarts.
    model_health_database_path: str = "database/model_health.db"

    # Optional specialist overrides. Empty values fall back to nvidia_default_model.
    nvidia_model_planner: str = ""
    nvidia_model_architect: str = ""
    nvidia_model_ui_ux: str = ""
    nvidia_model_frontend: str = ""
    nvidia_model_backend: str = ""
    nvidia_model_database: str = ""
    nvidia_model_security: str = ""
    nvidia_model_reviewer: str = ""
    nvidia_model_testing: str = ""
    nvidia_model_debugging: str = ""
    nvidia_model_performance: str = ""
    nvidia_model_integration: str = ""
    nvidia_model_sound_engineer: str = ""

    max_parallel_agents: int = Field(default=2, ge=1, le=16)
    max_agent_calls: int = Field(default=20, ge=1)
    max_agent_retries: int = Field(default=2, ge=0, le=10)
    max_repair_cycles: int = Field(default=3, ge=0, le=10)
    request_timeout_seconds: float = Field(default=120, gt=0, le=600)

    def model_for_agent(self, agent_id: str) -> str:
        """Resolve a specialist model override, falling back to the default model."""
        setting_name = f"nvidia_model_{agent_id.replace('-', '_')}"
        override = getattr(self, setting_name, "")
        if isinstance(override, str) and override.strip():
            return override.strip()
        return self.nvidia_default_model.strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()
