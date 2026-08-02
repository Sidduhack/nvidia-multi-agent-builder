-- Phase 4 persistence schema for PostgreSQL.
-- Secrets are intentionally not stored here. Model credentials belong in server-side secret storage.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE project_status AS ENUM ('draft','planning','running','failed','completed','cancelled');
CREATE TYPE task_status AS ENUM ('pending','planning','running','waiting','reviewing','testing','failed','repairing','completed','escalated','cancelled');
CREATE TYPE execution_status AS ENUM ('queued','running','failed','completed','cancelled');
CREATE TYPE build_status AS ENUM ('queued','running','failed','passed','cancelled');
CREATE TYPE file_operation AS ENUM ('create','modify','delete','rename');

CREATE TABLE users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    external_auth_id text UNIQUE NOT NULL,
    email text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE projects (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name text NOT NULL CHECK (length(name) BETWEEN 1 AND 200),
    prompt text NOT NULL,
    status project_status NOT NULL DEFAULT 'draft',
    current_version integer NOT NULL DEFAULT 0 CHECK (current_version >= 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_projects_owner_created ON projects(owner_id, created_at DESC);

CREATE TABLE agents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text UNIQUE NOT NULL,
    description text NOT NULL,
    enabled boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE model_configurations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id uuid REFERENCES users(id) ON DELETE CASCADE,
    provider text NOT NULL DEFAULT 'nvidia',
    model_id text NOT NULL,
    capabilities jsonb NOT NULL DEFAULT '[]'::jsonb,
    enabled boolean NOT NULL DEFAULT false,
    context_limit integer CHECK (context_limit IS NULL OR context_limit > 0),
    output_limit integer CHECK (output_limit IS NULL OR output_limit > 0),
    latency_class smallint NOT NULL DEFAULT 3 CHECK (latency_class BETWEEN 1 AND 5),
    cost_class smallint NOT NULL DEFAULT 1 CHECK (cost_class BETWEEN 1 AND 5),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(owner_id, provider, model_id)
);

CREATE TABLE tasks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    agent_id uuid REFERENCES agents(id) ON DELETE SET NULL,
    objective text NOT NULL CHECK (length(objective) BETWEEN 1 AND 4000),
    status task_status NOT NULL DEFAULT 'pending',
    context jsonb NOT NULL DEFAULT '{}'::jsonb,
    allowed_paths jsonb NOT NULL DEFAULT '[]'::jsonb,
    review_required boolean NOT NULL DEFAULT true,
    attempt integer NOT NULL DEFAULT 0 CHECK (attempt >= 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_tasks_project_status ON tasks(project_id, status);

CREATE TABLE task_dependencies (
    task_id uuid NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    depends_on_task_id uuid NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    PRIMARY KEY(task_id, depends_on_task_id),
    CHECK(task_id <> depends_on_task_id)
);

CREATE TABLE agent_executions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    task_id uuid NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    agent_id uuid REFERENCES agents(id) ON DELETE SET NULL,
    model_configuration_id uuid REFERENCES model_configurations(id) ON DELETE SET NULL,
    status execution_status NOT NULL DEFAULT 'queued',
    attempt integer NOT NULL DEFAULT 0 CHECK (attempt >= 0),
    duration_ms bigint CHECK (duration_ms IS NULL OR duration_ms >= 0),
    input_tokens bigint CHECK (input_tokens IS NULL OR input_tokens >= 0),
    output_tokens bigint CHECK (output_tokens IS NULL OR output_tokens >= 0),
    error_type text,
    summary text,
    started_at timestamptz,
    completed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_executions_task_created ON agent_executions(task_id, created_at DESC);

CREATE TABLE project_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version integer NOT NULL CHECK (version > 0),
    label text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(project_id, version)
);

CREATE TABLE generated_files (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version_id uuid REFERENCES project_versions(id) ON DELETE SET NULL,
    path text NOT NULL,
    content_hash text NOT NULL,
    size_bytes bigint NOT NULL DEFAULT 0 CHECK (size_bytes >= 0),
    operation file_operation NOT NULL,
    task_id uuid REFERENCES tasks(id) ON DELETE SET NULL,
    agent_id uuid REFERENCES agents(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(project_id, version_id, path)
);
CREATE INDEX idx_files_project_path ON generated_files(project_id, path);

CREATE TABLE builds (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version_id uuid REFERENCES project_versions(id) ON DELETE SET NULL,
    status build_status NOT NULL DEFAULT 'queued',
    sandbox_ref text,
    duration_ms bigint CHECK (duration_ms IS NULL OR duration_ms >= 0),
    error_summary text,
    created_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz
);

CREATE TABLE test_results (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    build_id uuid REFERENCES builds(id) ON DELETE CASCADE,
    task_id uuid REFERENCES tasks(id) ON DELETE SET NULL,
    suite text NOT NULL,
    passed integer NOT NULL DEFAULT 0 CHECK (passed >= 0),
    failed integer NOT NULL DEFAULT 0 CHECK (failed >= 0),
    skipped integer NOT NULL DEFAULT 0 CHECK (skipped >= 0),
    summary text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE project_logs (
    id bigserial PRIMARY KEY,
    project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    task_id uuid REFERENCES tasks(id) ON DELETE SET NULL,
    execution_id uuid REFERENCES agent_executions(id) ON DELETE SET NULL,
    event_type text NOT NULL,
    level text NOT NULL DEFAULT 'info' CHECK (level IN ('debug','info','warning','error')),
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_logs_project_created ON project_logs(project_id, created_at DESC);

CREATE TABLE project_memory (
    id bigserial PRIMARY KEY,
    project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    category text NOT NULL,
    value jsonb NOT NULL,
    source_task_id uuid REFERENCES tasks(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_memory_project_category ON project_memory(project_id, category, created_at);

-- Dependency cycles require graph-level validation in the application layer; the
-- relational constraint above prevents only direct self-dependencies.
