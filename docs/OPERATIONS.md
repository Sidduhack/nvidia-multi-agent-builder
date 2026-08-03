# Operations and Release Guide

## Configuration

Keep provider credentials and deployment secrets outside source control. Start from `.env.example` and inject real values through the deployment environment or a secret manager.

Before startup, verify that required model/provider configuration is present and that configured model identifiers are valid for the current NVIDIA service.

## Pre-merge verification

Backend:

```bash
ruff check app tests
pytest -q
```

Frontend:

```bash
cd frontend
npm ci
npm run typecheck
npm run build
```

Required CI must be green before merge.

## Runtime boundaries

The orchestration service and generated-project execution environment are separate trust zones. Do not replace the sandbox interface with unrestricted host subprocess execution in production.

Production sandbox implementations should enforce:

- isolated filesystem/workspace
- CPU, memory, process, and execution-time limits
- bounded stdout/stderr
- explicit network policy
- no implicit access to host or provider secrets
- auditable execution lifecycle
- cleanup after execution

## Incident handling

When an agent/provider/build/test operation fails:

1. Preserve the task and workspace state.
2. Record a sanitized error.
3. Retry only within configured limits.
4. Route to debugging/repair when appropriate.
5. Re-run the smallest relevant verification.
6. Escalate repeated failures instead of looping indefinitely.

Never include credentials in an incident log or model repair prompt.

## Release checklist

A production release requires more than a passing unit-test suite. Verify:

- backend lint/tests green
- frontend typecheck/build green
- no unresolved merge conflicts
- no real credentials committed
- `.env.example` contains placeholders only
- current NVIDIA model IDs and API behavior verified against official documentation
- security gate enabled for generated projects
- real isolated sandbox configured for production
- resource/time/output limits configured
- CORS/authentication/authorization appropriate for the deployment
- persistent database migrations and backups reviewed when persistence is enabled
- logs are sanitized
- failure/retry limits are bounded
- rollback/version strategy is documented
- end-to-end project generation path is exercised in the target deployment environment

Phase 19 owns the final audit against this checklist.
