import json
from unittest.mock import patch

import pytest

from src.providers.nvidia import NVIDIAProvider, NVIDIAProviderConfig, NVIDIAProviderError


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(
            {"choices": [{"message": {"content": "provider-ok"}}]}
        ).encode()


def test_provider_builds_server_side_request():
    provider = NVIDIAProvider(
        NVIDIAProviderConfig(api_key="test-secret", timeout_seconds=3)
    )
    with patch("src.providers.nvidia.request.urlopen", return_value=FakeResponse()) as call:
        response = provider.chat_completion(
            model="vendor/model", messages=[{"role": "user", "content": "hello"}]
        )
    req = call.call_args.args[0]
    assert req.full_url == "https://integrate.api.nvidia.com/v1/chat/completions"
    assert req.get_header("Authorization") == "Bearer test-secret"
    assert NVIDIAProvider.assistant_text(response) == "provider-ok"


def test_provider_requires_key(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    with pytest.raises(NVIDIAProviderError, match="NVIDIA_API_KEY"):
        NVIDIAProviderConfig.from_env()


def test_extra_cannot_override_protected_fields():
    provider = NVIDIAProvider(NVIDIAProviderConfig(api_key="test-secret"))
    with pytest.raises(NVIDIAProviderError, match="cannot override"):
        provider.chat_completion(
            model="vendor/model",
            messages=[{"role": "user", "content": "hello"}],
            extra={"model": "other/model"},
        )
