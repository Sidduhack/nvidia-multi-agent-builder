import pytest

from app.orchestrator.retry import RetryExhaustedError, with_backoff


@pytest.mark.asyncio
async def test_retry_succeeds_after_transient_failures() -> None:
    attempts = 0

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RuntimeError("temporary")
        return "ok"

    result = await with_backoff(operation, retries=2, base_delay_seconds=0)
    assert result == "ok"
    assert attempts == 3


@pytest.mark.asyncio
async def test_retry_stops_at_configured_limit() -> None:
    attempts = 0

    async def operation() -> None:
        nonlocal attempts
        attempts += 1
        raise RuntimeError("still broken")

    with pytest.raises(RetryExhaustedError):
        await with_backoff(operation, retries=1, base_delay_seconds=0)
    assert attempts == 2
