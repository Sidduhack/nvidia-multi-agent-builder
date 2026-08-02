from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.api import ErrorResponse, ProjectCreateRequest, TaskResponse
from app.schemas.task import TaskStatus


def test_project_create_request_validates_name_and_prompt() -> None:
    request = ProjectCreateRequest(name="Gaming site", prompt="Build a responsive gaming site")
    assert request.name == "Gaming site"


@pytest.mark.parametrize(
    ("name", "prompt"),
    [("", "valid prompt"), ("valid", "")],
)
def test_project_create_request_rejects_empty_fields(name: str, prompt: str) -> None:
    with pytest.raises(ValidationError):
        ProjectCreateRequest(name=name, prompt=prompt)


def test_task_response_preserves_dependency_contract() -> None:
    dependency = uuid4()
    task = TaskResponse(
        id=uuid4(),
        project_id=uuid4(),
        agent="architect",
        objective="Design architecture",
        dependencies=[dependency],
        status=TaskStatus.WAITING,
        review_required=True,
    )
    assert task.dependencies == [dependency]


def test_error_response_has_safe_structured_shape() -> None:
    error = ErrorResponse(code="project_not_found", message="Project was not found")
    assert error.details == {}
