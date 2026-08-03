from app.core.config import Settings


def test_agent_model_falls_back_to_default() -> None:
    settings = Settings(nvidia_default_model="test/default")

    assert settings.model_for_agent("planner") == "test/default"
    assert settings.model_for_agent("sound-engineer") == "test/default"


def test_agent_model_uses_specialist_override() -> None:
    settings = Settings(
        nvidia_default_model="test/default",
        nvidia_model_frontend="test/frontend",
        nvidia_model_sound_engineer="test/audio",
    )

    assert settings.model_for_agent("frontend") == "test/frontend"
    assert settings.model_for_agent("sound-engineer") == "test/audio"
    assert settings.model_for_agent("backend") == "test/default"
