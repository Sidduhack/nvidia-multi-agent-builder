from app.agents.protocol import AgentIssue


def test_architecture_conflict_can_require_architect_review() -> None:
    issue = AgentIssue(
        type="architecture_conflict",
        description="Frontend wants an endpoint outside the approved API contract.",
        affected_files=["frontend/auth.ts"],
        proposed_solution="Return the contract to the architect for review.",
        requires_architect_review=True,
    )
    assert issue.requires_architect_review is True
