# Phase 8 — NVIDIA Provider Integration

Phase 8 integrates NVIDIA-hosted NIM models behind a reusable server-side provider boundary.

## Verified NVIDIA API contract

As of 2026-08-02, NVIDIA documents the hosted LLM base URL as `https://integrate.api.nvidia.com` and chat inference as `POST /v1/chat/completions`. Authentication uses an NVIDIA API key as a Bearer credential. Chat requests use an OpenAI-compatible messages/model payload, and supported models can stream responses with SSE.

The implementation must keep the API key server-side and read it from `NVIDIA_API_KEY`. The default base URL is configurable through `NVIDIA_BASE_URL` so the provider can later target another compatible NVIDIA deployment without changing agent code.

## Architecture

`Agent -> Model Router -> NVIDIAProvider -> NVIDIA hosted NIM API`

Agents never construct HTTP requests themselves. The provider owns authentication, timeout/error normalization, and response parsing. Model IDs are configuration, not agent implementation details.

## Model configuration

Do not hard-code a permanent model per role. Configure model IDs using server-side settings/environment variables such as `NVIDIA_MODEL_PLANNER`, `NVIDIA_MODEL_ARCHITECT`, `NVIDIA_MODEL_FRONTEND`, and corresponding role variables. Before selecting a model ID for production, verify that exact model on NVIDIA Build/API documentation.

## Security rules

- Never expose `NVIDIA_API_KEY` through frontend code or API responses.
- Never log Authorization headers or provider secrets.
- Never send provider credentials inside agent prompts.
- Use bounded request timeouts and controlled retry/backoff in the orchestration layer.
- Treat provider output as untrusted data.

## Phase 8 acceptance gate

1. Reusable provider adapter exists.
2. Provider settings are environment-driven.
3. Model routing remains configurable per role/capability.
4. Tests mock the NVIDIA endpoint; CI must not require a real key.
5. No real credential is committed.
6. Existing Python and frontend CI remain green.
