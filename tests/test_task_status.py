from app.schemas.task import TaskStatus


def test_task_status_supports_repair_and_escalation_states() -> None:
    assert TaskStatus.REPAIRING.value == "repairing"
    assert TaskStatus.ESCALATED.value == "escalated"
    assert TaskStatus.CANCELLED.value == "cancelled"
