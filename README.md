# NVIDIA Multi-Agent Builder

A free-first, production-oriented multi-agent software development platform built around specialized AI agents and configurable NVIDIA-hosted models.

## Current milestone: Phase 1 foundation

Implemented:

- FastAPI service foundation
- server-side environment configuration
- provider abstraction
- NVIDIA provider adapter
- runtime model registry
- capability-based model router
- structured task schemas
- dependency graph foundation
- initial tests
- GitHub Actions CI

No model ID is permanently hard-coded into an agent. The runtime registry and router are designed to select from models that are actually configured and available.

## Security rules

- Never commit `.env`.
- Never put `NVIDIA_API_KEY` in browser JavaScript.
- Never log API keys or authorization headers.
- Generated commands will eventually execute only through the sandbox/policy layer, never directly on the host.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the development API documentation.

Run checks:

```bash
ruff check app tests
pytest -q
```

## Architecture direction

```text
User
  -> Control API
  -> Orchestrator
  -> Task DAG
  -> Agent Registry
  -> Model Router
  -> NVIDIA Provider Adapter
  -> NVIDIA API

Agent output
  -> schema validation
  -> workspace policy
  -> review
  -> sandbox build/test
  -> repair loop
  -> final integration
```

## Next milestone

Phase 2 will add the agent registry, structured agent execution protocol, project memory/context builder, event model, orchestration scheduler, controlled retries, and NVIDIA model discovery integration.
