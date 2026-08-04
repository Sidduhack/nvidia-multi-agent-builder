from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import Settings
from app.execution import AgentExecutionService
from app.model_health import ModelHealthRegistry
from app.model_registry import VERIFIED_MODEL_ROUTES
from app.providers.nvidia import NvidiaProvider


def load_env_file() -> None:
    """Tiny .env loader that avoids python-dotenv stdin/Termux edge cases."""
    path = ROOT / ".env"
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def print_snapshot(health: ModelHealthRegistry) -> None:
    print("\nMODEL HEALTH")
    print("-" * 100)
    for item in sorted(health.snapshot(), key=lambda value: value.model):
        latency = (
            f"{item.average_latency_seconds:.2f}s"
            if item.average_latency_seconds is not None
            else "-"
        )
        print(
            f"{item.model:52} "
            f"state={item.state().value:9} "
            f"ok={item.success_count:<2} "
            f"fail={item.failure_count:<2} "
            f"avg={latency}"
        )


async def main() -> None:
    load_env_file()
    key = os.getenv("NVIDIA_API_KEY", "").strip()
    if not key:
        raise SystemExit("NVIDIA_API_KEY is missing. Put it in .env or export it first.")

    # Keep this live diagnostic quick enough for Termux. A failing endpoint should
    # not consume several 600-second attempts before the fallback layer can react.
    settings = Settings(
        nvidia_api_key=key,
        request_timeout_seconds=float(os.getenv("LIVE_HEALTH_TIMEOUT", "90")),
        max_agent_retries=0,
    )
    provider = NvidiaProvider(settings)
    health = ModelHealthRegistry(failure_threshold=1, cooldown_seconds=300)
    service = AgentExecutionService(
        provider,
        default_model=settings.nvidia_default_model,
        model_health=health,
    )

    agent_id = os.getenv("LIVE_HEALTH_AGENT", "frontend").strip()
    route = VERIFIED_MODEL_ROUTES[agent_id]

    print("=== NVIDIA LIVE MODEL HEALTH TEST ===")
    print(f"Agent      : {agent_id}")
    print(f"Route      : {' -> '.join(route.candidates)}")
    print(f"Timeout    : {settings.request_timeout_seconds:g}s per model")
    print("API key    : loaded")

    print("\n[1/3] First real request")
    first = await service.execute(
        agent_id,
        "Reply with exactly: LIVE HEALTH REQUEST ONE",
    )
    print(f"Selected   : {first.model}")
    print(f"Output     : {first.content[:300]}")
    print_snapshot(health)

    print("\n[2/3] Second real request using learned health/latency")
    ordered = health.order_candidates(route.candidates)
    print(f"Next order : {' -> '.join(ordered)}")
    second = await service.execute(
        agent_id,
        "Reply with exactly: LIVE HEALTH REQUEST TWO",
    )
    print(f"Selected   : {second.model}")
    print(f"Output     : {second.content[:300]}")
    print_snapshot(health)

    print("\n[3/3] Deterministic cooldown proof")
    # Do not waste an NVIDIA request merely to manufacture an outage. Mark the
    # configured primary unhealthy locally, then prove the same routing algorithm
    # removes it from the next candidate list.
    health.record_failure(route.primary)
    after_failure = health.order_candidates(route.candidates)
    print(f"Failed     : {route.primary}")
    print(f"New order  : {' -> '.join(after_failure)}")
    if len(route.candidates) > 1 and route.primary in after_failure:
        raise SystemExit("FAILED: cooling-down primary was not skipped")

    print("\n=== LIVE HEALTH ROUTING VERIFIED ===")


if __name__ == "__main__":
    asyncio.run(main())
