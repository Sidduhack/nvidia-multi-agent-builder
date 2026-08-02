from src.model_service import ModelService


class FakeProvider:
    def chat_completion(self, **kwargs):
        assert kwargs["model"] == "vendor/planner"
        return {"choices": [{"message": {"content": "planned"}}]}

    @staticmethod
    def assistant_text(response):
        return response["choices"][0]["message"]["content"]


def test_service_routes_role_before_provider_call(monkeypatch):
    monkeypatch.setenv("NVIDIA_MODEL_PLANNER", "vendor/planner")
    service = ModelService(provider=FakeProvider())
    text, route = service.complete(
        role="planner", messages=[{"role": "user", "content": "plan"}]
    )
    assert text == "planned"
    assert route.model == "vendor/planner"
