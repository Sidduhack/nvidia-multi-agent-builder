from app.agents.protocol import AgentOutput


def test_agent_output_has_safe_empty_defaults() -> None:
    output = AgentOutput(summary="done")
    assert output.decisions == []
    assert output.artifacts == {}
    assert output.issues == []
    assert output.suggested_tasks == []
