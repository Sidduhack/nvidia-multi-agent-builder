# Phase 2 — Agent Runtime

Phase 2 turns the Phase 1 primitives into a minimal multi-agent runtime.

## Runtime path

```text
TaskGraph
  -> Scheduler
  -> AgentRegistry
  -> scoped ProjectMemory
  -> ModelRouter
  -> AgentExecutor
  -> AIProvider
  -> validated AgentOutput
  -> ProjectMemory + EventBus
```

## Design rules

1. Agents are specialized definitions, not independent services.
2. Agents request capabilities; model IDs remain configurable.
3. Provider model discovery never guesses capabilities.
4. Each task receives scoped project context instead of the full conversation.
5. Agent responses are validated before they enter shared memory.
6. The scheduler bounds parallelism.
7. Events expose concise status/decisions, never hidden chain-of-thought.
8. Failures are recorded as task events without leaking provider credentials or raw authorization data.

## Current agents

- `planner`: requirements and dependency-aware planning; no application-code generation.
- `architect`: architecture/contracts/technical boundaries based on approved requirements.

Additional engineering agents will be registered after their contracts and workspace permissions are defined.

## Intentionally deferred

- persistent PostgreSQL project memory
- file operations and locking
- retry/backoff implementation
- sandbox execution
- UI dashboard/WebSocket delivery
- model capability administration
- security/testing/debugging agents

These are separate milestones so generated code never gains host execution privileges before the sandbox policy exists.
