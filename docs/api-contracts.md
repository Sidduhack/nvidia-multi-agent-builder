# Phase 5 API contracts

All application endpoints are versioned under `/api/v1`. Provider credentials are never accepted by project-generation endpoints and are never returned by public APIs.

## Projects

### `POST /api/v1/projects`
Creates a project and bootstraps its Planner -> Architect task graph.

Request:
```json
{"name":"Gaming site","prompt":"Build a professional gaming website..."}
```

Response: `201 Created` with the project resource.

### `GET /api/v1/projects/{project_id}`
Returns project state. Unknown IDs return a structured `404`.

### `GET /api/v1/projects/{project_id}/tasks`
Returns the project's task graph state in dependency-safe metadata form.

## Agents

### `GET /api/v1/agents`
Returns the configured specialized agent team and public runtime state. It must not expose system prompts, credentials, hidden reasoning, or provider authorization data.

## Events

The event contract uses `{project_id, type, payload, created_at}`. A later realtime phase may transport the same contract over WebSockets/SSE without changing the event shape.

## Errors

Errors exposed by application APIs use:
```json
{"code":"project_not_found","message":"Project was not found","details":{}}
```

Internal stack traces, provider responses containing sensitive material, credentials, and hidden model reasoning must not be returned to clients.

## Ownership boundary

Authentication is not implemented in this phase. Before these project endpoints are connected to persistent multi-user storage, every project lookup and mutation must be scoped to the authenticated owner. Direct anonymous database access is not part of this architecture.
