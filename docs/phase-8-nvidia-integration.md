# Phase 8 — NVIDIA integration

Verified against current NVIDIA documentation: hosted LLM NIM uses `https://integrate.api.nvidia.com` and `POST /v1/chat/completions`, with Bearer authentication and an OpenAI-compatible request shape. Compatible models support streaming.

Architecture: Agent -> Model Router -> Model Registry -> NVIDIA Provider -> NVIDIA NIM API.

Secrets remain server-side. `.env.example` contains names/defaults only. The provider has bounded retry for 429/5xx and transport failures, timeouts, and sanitized errors. Model IDs are configuration so availability changes do not require agent rewrites.

The initial fallback `openai/gpt-oss-120b` is currently shown on NVIDIA Build with a free prototype endpoint. Per-agent model overrides are supported through `NVIDIA_MODEL_<AGENT>`.
