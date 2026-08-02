import asyncio

from app.testing import TestCase, TestKind, TestRunner, TestStatus


class FakeExecutor:
    async def run(
        self, command: tuple[str, ...], timeout_seconds: float
    ) -> tuple[int, str, str]:
        if command[0] == "fail":
            return 1, "", "assertion failed"
        if command[0] == "slow":
            await asyncio.sleep(timeout_seconds * 2)
        if command[0] == "explode":
            raise RuntimeError("sensitive executor detail")
        return 0, "ok", ""


async def test_pass_and_failure_are_recorded() -> None:
    runner = TestRunner(FakeExecutor())
    passed = await runner.run_case(TestCase("u1", "unit", TestKind.UNIT, ("pass",)))
    failed = await runner.run_case(TestCase("u2", "unit", TestKind.UNIT, ("fail",)))

    assert passed.status is TestStatus.PASSED
    assert failed.status is TestStatus.FAILED
    assert failed.exit_code == 1


async def test_timeout_is_bounded() -> None:
    runner = TestRunner(FakeExecutor())
    result = await runner.run_case(
        TestCase("slow", "slow test", TestKind.INTEGRATION, ("slow",), 0.01)
    )
    assert result.status is TestStatus.TIMED_OUT
    assert result.exit_code is None


async def test_executor_exception_does_not_leak_message() -> None:
    runner = TestRunner(FakeExecutor())
    result = await runner.run_case(
        TestCase("err", "executor error", TestKind.BUILD, ("explode",))
    )
    assert result.status is TestStatus.ERROR
    assert "sensitive executor detail" not in result.stderr
    assert "RuntimeError" in result.stderr


async def test_output_is_truncated() -> None:
    class LoudExecutor:
        async def run(
            self, command: tuple[str, ...], timeout_seconds: float
        ) -> tuple[int, str, str]:
            return 0, "x" * 100, ""

    runner = TestRunner(LoudExecutor(), output_limit=10)
    result = await runner.run_case(TestCase("loud", "loud", TestKind.UNIT, ("pass",)))
    assert result.stdout.startswith("x" * 10)
    assert "truncated" in result.stdout


async def test_suite_preserves_case_order() -> None:
    runner = TestRunner(FakeExecutor())
    cases = [
        TestCase("one", "one", TestKind.UNIT, ("pass",)),
        TestCase("two", "two", TestKind.BUILD, ("fail",)),
    ]
    results = await runner.run_suite(cases, max_parallel=2)
    assert [result.test_id for result in results] == ["one", "two"]
