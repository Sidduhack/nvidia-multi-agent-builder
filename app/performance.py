from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Awaitable, Callable, Generic, Hashable, TypeVar

T = TypeVar("T")
K = TypeVar("K", bound=Hashable)


@dataclass(frozen=True, slots=True)
class PerformanceLimits:
    max_parallel_agents: int = 4
    cache_entries: int = 128
    cache_ttl_seconds: float = 60.0

    def __post_init__(self) -> None:
        if self.max_parallel_agents < 1:
            raise ValueError("max_parallel_agents must be positive")
        if self.cache_entries < 1:
            raise ValueError("cache_entries must be positive")
        if self.cache_ttl_seconds <= 0:
            raise ValueError("cache_ttl_seconds must be positive")


@dataclass(frozen=True, slots=True)
class PerformanceSnapshot:
    active: int
    peak_active: int
    completed: int
    failed: int
    cache_hits: int
    cache_misses: int


class TTLCache(Generic[K, T]):
    """Small bounded in-memory cache for reusable orchestration metadata."""

    def __init__(self, max_entries: int, ttl_seconds: float) -> None:
        self._max_entries = max_entries
        self._ttl = ttl_seconds
        self._values: OrderedDict[K, tuple[float, T]] = OrderedDict()

    def get(self, key: K) -> T | None:
        item = self._values.get(key)
        if item is None:
            return None
        created, value = item
        if time.monotonic() - created >= self._ttl:
            del self._values[key]
            return None
        self._values.move_to_end(key)
        return value

    def put(self, key: K, value: T) -> None:
        self._values[key] = (time.monotonic(), value)
        self._values.move_to_end(key)
        while len(self._values) > self._max_entries:
            self._values.popitem(last=False)


class PerformanceController:
    """Bounds concurrency and avoids repeated work without changing agent semantics."""

    def __init__(self, limits: PerformanceLimits | None = None) -> None:
        self.limits = limits or PerformanceLimits()
        self._semaphore = asyncio.Semaphore(self.limits.max_parallel_agents)
        self._cache: TTLCache[str, object] = TTLCache(
            self.limits.cache_entries, self.limits.cache_ttl_seconds
        )
        self._active = 0
        self._peak_active = 0
        self._completed = 0
        self._failed = 0
        self._cache_hits = 0
        self._cache_misses = 0

    async def run(self, operation: Callable[[], Awaitable[T]]) -> T:
        async with self._semaphore:
            self._active += 1
            self._peak_active = max(self._peak_active, self._active)
            try:
                result = await operation()
            except Exception:
                self._failed += 1
                raise
            else:
                self._completed += 1
                return result
            finally:
                self._active -= 1

    async def cached(self, key: str, operation: Callable[[], Awaitable[T]]) -> T:
        cached = self._cache.get(key)
        if cached is not None:
            self._cache_hits += 1
            return cached  # type: ignore[return-value]
        self._cache_misses += 1
        result = await self.run(operation)
        self._cache.put(key, result)
        return result

    def snapshot(self) -> PerformanceSnapshot:
        return PerformanceSnapshot(
            active=self._active,
            peak_active=self._peak_active,
            completed=self._completed,
            failed=self._failed,
            cache_hits=self._cache_hits,
            cache_misses=self._cache_misses,
        )
