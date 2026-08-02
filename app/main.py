from fastapi import FastAPI

from app.api.projects import router as projects_router
from app.core.config import get_settings

app = FastAPI(
    title="NVIDIA Multi-Agent Builder",
    version="0.1.0",
    description="Free-first orchestration API for a specialized multi-agent software team.",
)
app.include_router(projects_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/config/public")
async def public_config() -> dict[str, str | int]:
    settings = get_settings()
    # Deliberately expose only non-secret values.
    return {
        "environment": settings.app_env,
        "max_parallel_agents": settings.max_parallel_agents,
        "max_agent_calls": settings.max_agent_calls,
    }
