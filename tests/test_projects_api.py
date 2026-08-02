from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_and_fetch_project() -> None:
    response = client.post(
        "/api/v1/projects",
        json={
            "name": "Gaming platform",
            "prompt": "Build a professional gaming platform with authentication and an admin dashboard.",
        },
    )
    assert response.status_code == 201
    project = response.json()
    assert project["name"] == "Gaming platform"
    assert project["status"] == "created"

    fetched = client.get(f"/api/v1/projects/{project['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == project["id"]


def test_project_validation_rejects_short_prompt() -> None:
    response = client.post(
        "/api/v1/projects",
        json={"name": "Valid name", "prompt": "too short"},
    )
    assert response.status_code == 422


def test_missing_project_returns_404() -> None:
    response = client.get("/api/v1/projects/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_list_projects_does_not_expose_prompt() -> None:
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    for project in response.json():
        assert "prompt" not in project
