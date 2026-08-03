import asyncio
import json
from collections.abc import AsyncIterator

import httpx

from app.core.config import Settings
from app.providers.base import AIProvider, CompletionRequest, CompletionResponse


class NvidiaProviderError(RuntimeError):
    pass


class NvidiaProvider(AIProvider):
    """Server-side adapter for NVIDIA's OpenAI-compatible API surface."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _headers(self) -> dict[str, str]:
        if not self.settings.nvidia_api_key:
            raise NvidiaProviderError("NVIDIA_API_KEY is not configured")
        return {
            "Authorization": f"Bearer {self.settings.nvidia_api_key}",
            "Content-Type": "application/json",
        }

    def _payload(self, request: CompletionRequest, *, stream: bool) -> dict:
        payload = {
            "model": request.model,
            "messages": [message.model_dump() for message in request.messages],
            "temperature": request.temperature,
            "stream": stream,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        return payload

    @staticmethod
    def _retryable_status(status_code: int) -> bool:
        return status_code == 429 or status_code >= 500

    @staticmethod
    def _error_detail(response: httpx.Response) -> str:
        try:
            data = response.json()
            detail = data.get("detail") or data.get("message") or data.get("error")
            if isinstance(detail, dict):
                detail = detail.get("message") or str(detail)
            if detail:
                return str(detail)[:300]
        except (ValueError, TypeError):
            pass
        return response.text.strip()[:300] or "no response detail"

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        attempts = self.settings.max_agent_retries + 1
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                    response = await client.post(
                        f"{self.settings.nvidia_base_url.rstrip('/')}/chat/completions",
                        headers=self._headers(),
                        json=self._payload(request, stream=False),
                    )
            except httpx.TimeoutException as exc:
                last_error = exc
                if attempt < attempts:
                    await asyncio.sleep(min(2 ** (attempt - 1), 8))
                    continue
                raise NvidiaProviderError(
                    f"NVIDIA model {request.model} timed out after "
                    f"{self.settings.request_timeout_seconds:g}s on attempt {attempt}/{attempts}"
                ) from exc
            except httpx.RequestError as exc:
                last_error = exc
                if attempt < attempts:
                    await asyncio.sleep(min(2 ** (attempt - 1), 8))
                    continue
                raise NvidiaProviderError(
                    f"NVIDIA model {request.model} transport error after {attempt}/{attempts} attempts: "
                    f"{type(exc).__name__}"
                ) from exc

            if response.is_error:
                detail = self._error_detail(response)
                if self._retryable_status(response.status_code) and attempt < attempts:
                    retry_after = response.headers.get("retry-after")
                    try:
                        delay = min(float(retry_after), 30) if retry_after else min(2 ** (attempt - 1), 8)
                    except ValueError:
                        delay = min(2 ** (attempt - 1), 8)
                    await asyncio.sleep(delay)
                    continue
                raise NvidiaProviderError(
                    f"NVIDIA model {request.model} failed with HTTP {response.status_code} "
                    f"on attempt {attempt}/{attempts}: {detail}"
                )

            try:
                data = response.json()
                choice = data["choices"][0]
                content = choice["message"]["content"]
            except (ValueError, KeyError, IndexError, TypeError) as exc:
                raise NvidiaProviderError(
                    f"NVIDIA model {request.model} returned an invalid completion response"
                ) from exc

            if not isinstance(content, str):
                raise NvidiaProviderError(
                    f"NVIDIA model {request.model} completion response did not contain text content"
                )

            return CompletionResponse(
                model=data.get("model", request.model),
                content=content,
                usage=data.get("usage", {}),
            )

        raise NvidiaProviderError(
            f"NVIDIA model {request.model} request failed after {attempts} attempts: {last_error}"
        )

    async def stream(self, request: CompletionRequest) -> AsyncIterator[str]:
        try:
            async with (
                httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client,
                client.stream(
                    "POST",
                    f"{self.settings.nvidia_base_url.rstrip('/')}/chat/completions",
                    headers=self._headers(),
                    json=self._payload(request, stream=True),
                ) as response,
            ):
                if response.is_error:
                    raise NvidiaProviderError(
                        f"NVIDIA streaming request failed with HTTP {response.status_code}: "
                        f"{self._error_detail(response)}"
                    )
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    event = line[6:]
                    if event == "[DONE]":
                        break
                    data = json.loads(event)
                    delta = data.get("choices", [{}])[0].get("delta", {}).get("content")
                    if delta:
                        yield delta
        except httpx.TimeoutException as exc:
            raise NvidiaProviderError(
                f"NVIDIA model {request.model} streaming request timed out after "
                f"{self.settings.request_timeout_seconds:g} seconds"
            ) from exc
        except httpx.RequestError as exc:
            raise NvidiaProviderError(
                f"NVIDIA model {request.model} streaming transport error: {type(exc).__name__}"
            ) from exc

    async def list_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get(
                    f"{self.settings.nvidia_base_url.rstrip('/')}/models",
                    headers=self._headers(),
                )
        except httpx.TimeoutException as exc:
            raise NvidiaProviderError(
                f"NVIDIA model discovery timed out after {self.settings.request_timeout_seconds:g} seconds"
            ) from exc
        except httpx.RequestError as exc:
            raise NvidiaProviderError(f"NVIDIA model discovery transport error: {type(exc).__name__}") from exc

        if response.is_error:
            raise NvidiaProviderError(
                f"NVIDIA model discovery failed with HTTP {response.status_code}: {self._error_detail(response)}"
            )
        return [item["id"] for item in response.json().get("data", []) if "id" in item]
