from fastapi.testclient import TestClient

from app.main import app


def test_public_config_does_not_expose_nvidia_api_key() -> None:
    response = TestClient(app).get("/api/v1/config/public")
    assert response.status_code == 200
    serialized = response.text.lower()
    assert "nvidia_api_key" not in serialized
    assert "authorization" not in serialized
