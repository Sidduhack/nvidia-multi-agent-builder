from pathlib import Path


SCHEMA = Path("database/schema.sql").read_text()


def test_schema_contains_required_persistence_tables() -> None:
    required = {
        "users",
        "projects",
        "agents",
        "model_configurations",
        "tasks",
        "task_dependencies",
        "agent_executions",
        "generated_files",
        "builds",
        "test_results",
        "project_logs",
        "project_versions",
        "project_memory",
    }
    for table in required:
        assert f"CREATE TABLE {table} (" in SCHEMA


def test_schema_does_not_define_provider_secret_columns() -> None:
    lowered = SCHEMA.lower()
    forbidden_columns = [
        "api_key text",
        "password text",
        "access_token text",
        "refresh_token text",
        "bearer_token text",
    ]
    for column in forbidden_columns:
        assert column not in lowered


def test_task_dependencies_reject_direct_self_dependency() -> None:
    assert "CHECK(task_id <> depends_on_task_id)" in SCHEMA


def test_core_project_tables_cascade_with_project_deletion() -> None:
    assert SCHEMA.count("REFERENCES projects(id) ON DELETE CASCADE") >= 8
