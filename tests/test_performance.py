import asyncio

import pytest

from app.performance import PerformanceController, PerformanceLimits, TTLCache


def test_invalid_limits_are_rejected() -> None:
    with pytest.raises(ValueError):
        PerformanceLimits(max_parallel_agents=0)


def test_cache_is_bounded_lru() -> None:
    cache: TTLCache[str, str] = TTLCache(max_entries=2, ttl_seconds=60)
    cache.put("a", "A")
    cache.put("b", "B")
    assert cache.get("a") == "A"
    cache.put("c", "C")
    assert cache.get("b") is None
    assert cache.get("a") == "A"
    assert cache.get("c") == "C"


async def test_parallel_work_is_bounded() -> None:
    controller = PerformanceController(PerformanceLimits(max_parallel_agents=2))
    active = 0
    peak = 0
    lock = asyncio.Lock()

    async def work() -> int:
        nonlocal active, peak
        async with lock:
            active += 1
            peak = max(peak, active)
        await asyncio.sleep(0.01)
        async with lock:
            active -= 1
        return 1

    results = await asyncio.gather(*(controller.run(work) for _ in range(6)))
    assert results == [1] * 6
    assert peak == 2
    assert controller.snapshot().peak_active == 2
    assert controller.snapshot().completed == 6


async def test_cached_operation_avoids_duplicate_sequential_call() -> None:
    controller = PerformanceController()
    calls = 0

    async def work() -> str:
        nonlocal calls
        calls += 1
        return "result"

    assert await controller.cached("architecture:1", work) == "result"
    assert await controller.cached("architecture:1", work) == "result"
    assert calls == 1
    snapshot = controller.snapshot()
    assert snapshot.cache_hits == 1
    assert snapshot.cache_misses == 1


async def test_failures_are_measured_and_propagated() -> None:
    controller = PerformanceController()

    async def fail() -> None:
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await controller.run(fail)
    snapshot = controller.snapshot()
    assert snapshot.failed == 1
    assert snapshot.active == 0
