from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from time import monotonic

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import Settings
from app.model_health import ModelHealthRegistry
from app.model_registry import VERIFIED_MODEL_ROUTES
from app.providers.base import ChatMessage, CompletionRequest
from app.providers.nvidia import NvidiaProvider


def load_env_file() -> None:
    path = ROOT / ".env"
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


async def probe(
    provider: NvidiaProvider,
    health: ModelHealthRegistry,
    model: str,
) -> tuple[str, str, float | None, str]:
    request = CompletionRequest(
        model=model,
        messages=[ChatMessage(role="user", content="Reply with exactly: BENCHMARK OK")],
        temperature=0.0,
        max_tokens=512,
    )
    started = monotonic()
    try:
        response = await provider.complete(request)
    except Exception as exc:
        elapsed = monotonic() - started
        health.record_failure(model)
        return model, "FAILED", elapsed, f"{type(exc).__name__}: {exc}"

    elapsed = monotonic() - started
    health.record_success(model, elapsed)
    return model, "WORKING", elapsed, response.content.strip()[:120]


async def main() -> None:
    load_env_file()
    key = os.getenv("NVIDIA_API_KEY", "").strip()
    if not key:
        raise SystemExit("NVIDIA_API_KEY is missing")

    agent_id = os.getenv("LIVE_BENCHMARK_AGENT", "frontend").strip()
    if agent_id not in VERIFIED_MODEL_ROUTES:
        raise SystemExit(f"Unknown agent route: {agent_id}")

    timeout = float(os.getenv("LIVE_BENCHMARK_TIMEOUT", "90"))
    settings = Settings(
        nvidia_api_key=key,
        request_timeout_seconds=timeout,
        max_agent_retries=0,
    )
    provider = NvidiaProvider(settings)
    health = ModelHealthRegistry(failure_threshold=1, cooldown_seconds=300)
    route = VERIFIED_MODEL_ROUTES[agent_id]

    print("=== NVIDIA LIVE MULTI-MODEL BENCHMARK ===")
    print(f"Agent       : {agent_id}")
    print(f"Candidates  : {len(route.candidates)}")
    print(f"Timeout     : {timeout:g}s/model")
    print("Execution   : CONCURRENT")
    print("\nLaunching one small real request per candidate...\n")

    results = await asyncio.gather(
        *(probe(provider, health, model) for model in route.candidates)
    )

    print("=" * 118)
    print("RESULTS")
    print("=" * 118)
    for model, status, elapsed, detail in results:
        elapsed_text = f"{elapsed:7.2f}s" if elapsed is not None else "      -"
        print(f"{status:8} | {elapsed_text} | {model}")
        print(f"           {detail}")

    ranked = health.order_candidates(route.candidates)
    print("\nLEARNED ROUTE")
    print("-------------")
    for index, model in enumerate(ranked, 1):
        item = health.get(model)
        latency = (
            f"{item.average_latency_seconds:.2f}s"
            if item.average_latency_seconds is not None
            else "unmeasured"
        )
        print(f"{index}. {model} | {item.state().value} | avg={latency}")

    cooling = [model for model in route.candidates if not health.available(model)]
    if cooling:
        print("\nCOOLDOWN / SKIPPED")
        print("------------------")
        for model in cooling:
            print(f"- {model}")

    working = sum(1 for _, status, _, _ in results if status == "WORKING")
    print(f"\nWorking: {working}/{len(results)}")
    if working == 0:
        raise SystemExit("FAILED: no candidate model completed successfully")
    print("=== LIVE MULTI-MODEL BENCHMARK COMPLETE ===")


if __name__ == "__main__":
    asyncio.run(main())
