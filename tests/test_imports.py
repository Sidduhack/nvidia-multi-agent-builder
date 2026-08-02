import importlib


def test_core_packages_import() -> None:
    modules = [
        "app.agents.definitions",
        "app.agents.executor",
        "app.events.bus",
        "app.memory.project",
        "app.models.discovery",
        "app.orchestrator.bootstrap",
        "app.orchestrator.scheduler",
    ]
    for module in modules:
        assert importlib.import_module(module) is not None
