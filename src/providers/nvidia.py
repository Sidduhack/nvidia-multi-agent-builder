"""Reusable server-side adapter for NVIDIA hosted NIM chat models."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from urllib import error, request


class NVIDIAProviderError(RuntimeError):
    """Normalized provider failure safe for orchestration code to handle."""


@dataclass(frozen=True)
class NVIDIAProviderConfig:
    api_key: str
    base_url: str = "https://integrate.api.nvidia.com/v1"
    timeout_seconds: float = 60.0

    @classmethod
    def from_env(cls) -> "NVIDIAProviderConfig":
        api_key = os.getenv("NVIDIA_API_KEY", "").strip()
        if not api_key:
            raise NVIDIAProviderError("NVIDIA_API_KEY is not configured")
        base_url = os.getenv(
            "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
        ).rstrip("/")
        try:
            timeout = float(os.getenv("NVIDIA_REQUEST_TIMEOUT_SECONDS", "60"))
        except ValueError as exc:
            raise NVIDIAProviderError(
                "NVIDIA_REQUEST_TIMEOUT_SECONDS must be numeric"
            ) from exc
        if timeout <= 0:
            raise NVIDIAProviderError(
                "NVIDIA_REQUEST_TIMEOUT_SECONDS must be greater than zero"
            )
        return cls(api_key=api_key, base_url=base_url, timeout_seconds=timeout)


class NVIDIAProvider:
    """OpenAI-compatible NVIDIA NIM chat-completions provider boundary."""

    def __init__(self, config: NVIDIAProviderConfig | None = None) -> None:
        self.config = config or NVIDIAProviderConfig.from_env()

    def chat_completion(
        self,
        *,
        model: str,
        messages: Sequence[Mapping[str, Any]],
        max_tokens: int | None = None,
        temperature: float | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        if not model.strip():
            raise NVIDIAProviderError("A model ID is required")
        if not messages:
            raise NVIDIAProviderError("At least one chat message is required")

        payload: dict[str, Any] = {
            "model": model,
            "messages": list(messages),
            "stream": False,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if temperature is not None:
            payload["temperature"] = temperature
        if extra:
            protected = {"model", "messages", "stream"}
            overlap = protected.intersection(extra)
            if overlap:
                raise NVIDIAProviderError(
                    "extra parameters cannot override: " + ", ".join(sorted(overlap))
                )
            payload.update(extra)

        body = json.dumps(payload).encode("utf-8")
        http_request = request.Request(
            f"{self.config.base_url}/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        try:
            with request.urlopen(
                http_request, timeout=self.config.timeout_seconds
            ) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            # Deliberately omit response bodies and credentials from errors/logs.
            raise NVIDIAProviderError(
                f"NVIDIA API request failed with HTTP {exc.code}"
            ) from exc
        except (error.URLError, TimeoutError) as exc:
            raise NVIDIAProviderError("NVIDIA API request failed") from exc

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise NVIDIAProviderError("NVIDIA API returned invalid JSON") from exc
        if not isinstance(parsed, dict):
            raise NVIDIAProviderError("NVIDIA API returned an unexpected response")
        return parsed

    @staticmethod
    def assistant_text(response: Mapping[str, Any]) -> str:
        """Extract assistant text without leaking the provider response upstream."""
        try:
            content = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise NVIDIAProviderError("NVIDIA response has no assistant message") from exc
        if not isinstance(content, str):
            raise NVIDIAProviderError("NVIDIA assistant content is not text")
        return content
