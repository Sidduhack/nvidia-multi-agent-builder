# Database architecture

Phase 4 defines the persistent state required by the multi-agent builder.

## PostgreSQL

PostgreSQL is the source of truth for users, projects, task DAG metadata, agent executions, model metadata, generated-file metadata, builds, tests, logs, versions, and structured project memory.

The initial schema lives in `database/schema.sql`. It is deliberately plain PostgreSQL so it can run on a local PostgreSQL instance or a compatible hosted service such as Supabase without locking the application to a vendor-specific client.

## Secret boundary

API keys, passwords, bearer tokens, and provider credentials MUST NOT be stored in `model_configurations`, `project_memory`, or `project_logs`.

`model_configurations` stores only non-secret routing metadata. Provider credentials remain in server-side environment/secret management.

## Generated files

The database stores generated-file metadata and content hashes. Large workspace contents should live in the controlled workspace/object-storage layer rather than being duplicated into database rows. Project versions provide immutable checkpoint metadata.

## Task graph

`task_dependencies` represents DAG edges. SQL prevents direct self-dependencies. Full cycle detection remains in the application `TaskGraph`, where arbitrary graph cycles can be rejected before persistence.

## Access model

Every project is owned by a user. Application queries must scope project resources through the authenticated owner/project relationship. Database-level row policies can be added when the authentication provider is selected; until then, the backend is responsible for enforcing ownership and must not expose direct anonymous database access.

## Retention

Logs and execution history can grow rapidly. A later operations phase should define retention/archival windows and redact sensitive fields before persistence.
