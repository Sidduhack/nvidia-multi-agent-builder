def test_core_packages_import() -> None:
    import app.agents.definitions  # noqa: F401
    import app.agents.executor  # noqa: F401
    import app.events.bus  # noqa: F401
    import app.memory.project  # noqa: F401
    import app.models.discovery  # noqa: F401
    import app.orchestrator.bootstrap  # noqa: F401
    import app.orchestrator.scheduler  # noqa: F401
