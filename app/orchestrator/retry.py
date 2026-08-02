import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


class RetryExhaustedError(RuntimeError):
    pass


async def with_backoff(
    operation: Callable[[], Awaitable[T]],
    *,
    retries: int,
    base_delay_seconds: float = 0.25,
    retryable: tuple[type[Exception], ...] = (RuntimeError,),
) -> T:
    """Retry explicitly retryable transient operations with bounded backoff."""
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return await operation()
        except retryable as exc:
            last_error = exc
            if attempt >= retries:
                break
            await asyncio.sleep(base_delay_seconds * (2**attempt))
    raise RetryExhaustedError(f"Operation failed after {retries + 1} attempts") from last_error
