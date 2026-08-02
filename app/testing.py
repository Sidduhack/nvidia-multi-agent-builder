from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class TestKind(StrEnum):
    UNIT = "unit"
    INTEGRATION = "integration"
    BUILD = "build"
    END_TO_END = "end_to_end"


class TestStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class TestCase:
    id: str
    name: str
    kind: TestKind
    command: tuple[str, ...]
    timeout_seconds: float = 120.0


@dataclass(frozen=True, slots=True)
class TestResult:
    test_id: str
    status: TestStatus
    duration_seconds: float
    exit_code: int | None
    stdout: str
    stderr: str


class CommandExecutor(Protocol):
    async def run(
        self, command: tuple[str, ...], timeout_seconds: float
    ) -> tuple[int, str, str]: ...


class TestRunner:
    """Runs approved test commands through an injected isolated executor."""

    def __init__(self, executor: CommandExecutor, *, output_limit: int = 20_000) -> None:
        if output_limit < 1:
            raise ValueError("output_limit must be positive")
        self.executor = executor
        self.output_limit = output_limit

    def _bounded(self, value: str) -> str:
        if len(value) <= self.output_limit:
            return value
        return value[: self.output_limit] + "\n...[output truncated]"

    async def run_case(self, case: TestCase) -> TestResult:
        if not case.command:
            raise ValueError("test command cannot be empty")
        if case.timeout_seconds <= 0:
            raise ValueError("timeout must be positive")

        started = time.monotonic()
        try:
            exit_code, stdout, stderr = await asyncio.wait_for(
                self.executor.run(case.command, case.timeout_seconds),
                timeout=case.timeout_seconds,
            )
            status = TestStatus.PASSED if exit_code == 0 else TestStatus.FAILED
        except TimeoutError:
            exit_code, stdout, stderr = None, "", "Test execution timed out"
            status = TestStatus.TIMED_OUT
        except Exception as exc:  # noqa: BLE001 -- executor is a trust boundary
            exit_code, stdout = None, ""
            stderr = f"Executor error: {type(exc).__name__}"
            status = TestStatus.ERROR

        return TestResult(
            test_id=case.id,
            status=status,
            duration_seconds=round(time.monotonic() - started, 4),
            exit_code=exit_code,
            stdout=self._bounded(stdout),
            stderr=self._bounded(stderr),
        )

    async def run_suite(
        self, cases: list[TestCase], *, max_parallel: int = 4
    ) -> list[TestResult]:
        if max_parallel < 1:
            raise ValueError("max_parallel must be positive")
        semaphore = asyncio.Semaphore(max_parallel)

        async def guarded(case: TestCase) -> TestResult:
            async with semaphore:
                return await self.run_case(case)

        return list(await asyncio.gather(*(guarded(case) for case in cases)))
