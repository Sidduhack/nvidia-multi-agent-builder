from app.sound_engineer import SOUND_ENGINEER


def test_sound_engineer_has_stable_identity_and_collaborators() -> None:
    assert SOUND_ENGINEER.agent_id == "sound-engineer"
    assert SOUND_ENGINEER.display_name == "Sound Engineer"
    assert {"ui-ux", "frontend", "performance"}.issubset(SOUND_ENGINEER.collaborators)


def test_sound_engineer_covers_audio_system_work() -> None:
    responsibilities = " ".join(SOUND_ENGINEER.responsibilities).lower()
    assert "web audio" in responsibilities
    assert "animation" in responsibilities
    assert "volume" in responsibilities
    assert "audio assets" in responsibilities


def test_sound_engineer_does_not_pretend_to_synthesize_assets() -> None:
    guardrails = " ".join(SOUND_ENGINEER.guardrails).lower()
    assert "never claim an audio file was synthesized" in guardrails
    assert "never fabricate licenses" in guardrails
    assert "autoplay" in guardrails
    assert "credentials" in guardrails
