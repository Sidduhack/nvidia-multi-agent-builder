import pytest

from src.model_router import ModelRoutingError, route_model


def test_role_model_has_priority(monkeypatch):
    monkeypatch.setenv("NVIDIA_MODEL_DEFAULT", "vendor/default")
    monkeypatch.setenv("NVIDIA_MODEL_FRONTEND", "vendor/frontend")
    route = route_model("frontend")
    assert route.model == "vendor/frontend"
    assert route.source == "NVIDIA_MODEL_FRONTEND"


def test_default_model_is_fallback(monkeypatch):
    monkeypatch.delenv("NVIDIA_MODEL_BACKEND", raising=False)
    monkeypatch.setenv("NVIDIA_MODEL_DEFAULT", "vendor/default")
    assert route_model("backend").model == "vendor/default"


def test_missing_model_is_explicit(monkeypatch):
    monkeypatch.delenv("NVIDIA_MODEL_SECURITY", raising=False)
    monkeypatch.delenv("NVIDIA_MODEL_DEFAULT", raising=False)
    with pytest.raises(ModelRoutingError, match="No NVIDIA model configured"):
        route_model("security")


def test_unknown_role_is_rejected():
    with pytest.raises(ModelRoutingError, match="Unknown agent role"):
        route_model("unknown")
