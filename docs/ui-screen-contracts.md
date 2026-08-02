# UI screen contracts

The frontend implementation must use approved `/api/v1` contracts and must not invent server behavior.

| Surface | Required data | Primary states |
| --- | --- | --- |
| Projects | project summaries (future list contract) | empty, loading, loaded, error |
| Project Overview | project, tasks, agents, events | planning, active, blocked, failed, completed |
| Agents | agent status list | idle, active, waiting, failed |
| Tasks | task responses | pending through completed/escalated |
| Files | generated file metadata (future contract) | empty, loading, version selected, error |
| Logs | project events/logs (future paginated contract) | loading, live/reconnecting, filtered, error |
| Tests | test results (future contract) | not run, running, passed, failed |
| Preview | build/sandbox metadata (future contract) | unavailable, building, running, failed, stopped |
| Settings | public model/limit configuration (future contract) | loading, saved, validation error |

## Contract gaps intentionally identified

Phase 5 already defines project creation, project state, task state, agent status, event shape, and safe error shape. Before frontend implementation connects the remaining screens, backend/API work must define:

- project list/pagination
- generated file tree/content retrieval
- structured/paginated logs
- build and preview status
- test result retrieval
- public model configuration and usage/limits
- pause/cancel/retry actions
- authentication/session/ownership behavior
- realtime event transport

The frontend must render unavailable features honestly until these contracts exist. It must not fabricate successful builds, tests, preview URLs, model usage, or persistence.

## Mobile priority

On mobile the default order is Overview -> Tasks -> Files -> Preview -> More. Agent activity is surfaced inside Overview and through More/Agents so the primary navigation remains compact.
