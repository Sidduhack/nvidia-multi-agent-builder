from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


def run_python(code: str, database: Path) -> str:
    result = subprocess.run(
        [sys.executable, "-c", code, str(database)],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        database = Path(tmp) / "model-health.db"

        process_a = r'''
import sys

from app.model_health import ModelHealthRegistry
from app.sqlite_model_health_store import SQLiteModelHealthStore

db = sys.argv[1]
registry = ModelHealthRegistry(
    store=SQLiteModelHealthStore(db),
    failure_threshold=2,
)

registry.record_success("model/slow", 30.0)
registry.record_success("model/fast", 2.0)

print("A ORDER:", " -> ".join(
    registry.order_candidates(("model/slow", "model/fast"))
))
'''

        process_b = r'''
import sys

from app.model_health import ModelHealthRegistry
from app.sqlite_model_health_store import SQLiteModelHealthStore

db = sys.argv[1]

registry = ModelHealthRegistry(
    store=SQLiteModelHealthStore(db),
    failure_threshold=2,
)

slow = registry.get("model/slow")
fast = registry.get("model/fast")

print("B SLOW:", slow.success_count, slow.average_latency_seconds)
print("B FAST:", fast.success_count, fast.average_latency_seconds)

order = registry.order_candidates(("model/slow", "model/fast"))
print("B ORDER:", " -> ".join(order))

assert slow.success_count == 1
assert fast.success_count == 1
assert slow.average_latency_seconds == 30.0
assert fast.average_latency_seconds == 2.0
assert order == ("model/fast", "model/slow")

print("RESTART PERSISTENCE VERIFIED")
'''

        print("=== PROCESS A: LEARN ===")
        print(run_python(process_a, database))

        print()
        print("Process A terminated.")
        print("Starting completely new Python process...")
        print()

        print("=== PROCESS B: RELOAD ===")
        print(run_python(process_b, database))

        print()
        print("=== CROSS-PROCESS MODEL INTELLIGENCE VERIFIED ===")


if __name__ == "__main__":
    main()
