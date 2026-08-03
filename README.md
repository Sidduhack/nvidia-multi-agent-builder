# NVIDIA Multi-Agent Builder

A free-first, production-oriented multi-agent software-development platform built around specialized AI agents and configurable NVIDIA-hosted models.

## Status

Phases 1–17 establish the platform foundation: orchestration, specialized agents, persistent project state, API contracts, dashboard architecture, NVIDIA provider/model routing, workspace management, testing, sandbox/security boundaries, integration validation, and bounded performance controls.

Phase 18 documents how those pieces fit together. Phase 19 is the final production-readiness audit.

## Architecture

```text
User / Dashboard
      |
      v
Control API / Orchestrator
      |
      +--> Project Memory + Task DAG + Event Log
      |
      +--> Agent Registry
             |
             +--> Planner / Architect / UI-UX
             +--> Frontend / Backend / Database
             +--> Security / Reviewer / Testing / Debugging
             +--> Performance / Final Integration
                      |
                      v
                Model Router
                      |
                Model Registry
                      |
             NVIDIA Provider Adapter
                      |
                  NVIDIA API

Generated changes
      -> structured workspace
      -> security review
      -> restricted sandbox
      -> tests/build
      -> repair/review loop
      -> integration result
```

Agents are specialized. They receive least-context task inputs rather than the entire project conversation, and model assignment remains configurable instead of being permanently tied to one model.

## Core safety model

AI output is untrusted input. Generated files and commands must pass through the workspace, security, and sandbox layers before execution.

- Keep NVIDIA and other provider credentials server-side.
- Never commit `.env` or real secrets.
- Never expose provider keys in browser JavaScript, logs, generated projects, or model prompts unless strictly required.
- Do not execute generated shell commands directly on the production host.
- Preserve filesystem boundaries, execution timeouts, output limits, and sandbox policy.
- Treat hard-coded credentials and security findings as execution blockers.
- Preserve project revisions so conflicting agent writes cannot silently overwrite state.

## Local backend setup

Requirements: a supported Python version, `pip`, and a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
```

Put local credentials only in `.env`. Never commit that file.

Start the API:

```bash
uvicorn app.main:app --reload
```

Development API documentation is then available at `http://127.0.0.1:8000/docs`.

## Frontend

The frontend is a React + TypeScript + Vite dashboard foundation. Install and build it from the frontend directory using the package scripts committed with the project.

```bash
cd frontend
npm ci
npm run typecheck
npm run build
```

Use `npm run dev` for local dashboard development when available in the package scripts.

The dashboard is intended to expose project progress, agents, tasks, files, logs, tests, preview state, and settings without exposing hidden model chain-of-thought. Surface concise decisions, actions, tool results, failures, and repair status instead.

## NVIDIA provider and model routing

The provider path is intentionally layered:

```text
Agent -> Model Router -> Model Registry -> NVIDIA Provider Adapter -> NVIDIA API
```

This prevents individual agents from duplicating provider HTTP logic and makes model replacement possible without rewriting agent behavior.

Configure credentials and provider settings through server-side environment configuration. `.env.example` documents supported variables without containing real credentials.

Model IDs must correspond to models actually configured and available through the current NVIDIA service. Do not invent model identifiers or assume every model supports the same context size, streaming, tools, or structured output.

## Agent execution lifecycle

A normal project follows this lifecycle:

```text
prompt
 -> requirements
 -> architecture
 -> task dependency graph
 -> specialized agent execution
 -> controlled workspace changes
 -> code review
 -> security gate
 -> sandbox build/test
 -> debugging/repair when required
 -> integration
 -> final result
```

Independent tasks may execute concurrently, but dependencies and file ownership take priority over raw parallelism. Repair loops are bounded so a failing model cannot create an infinite agent conversation.

## Workspace and project state

Generated project state is represented through controlled file operations and revisions. Agents should identify the task, agent, affected path, and reason for a change. Conflicting revisions must be detected rather than silently overwritten.

Persistent project data includes project/task state, dependencies, agent executions, generated-file metadata, builds, test results, logs, and versions/checkpoints as the corresponding persistence layers are enabled.

## Testing and CI

Backend checks:

```bash
ruff check app tests
pytest -q
```

Frontend checks:

```bash
cd frontend
npm ci
npm run typecheck
npm run build
```

GitHub Actions is the merge gate. A pull request should not be merged while required checks are red. Never claim a generated project or platform change passed tests unless those tests were actually executed successfully.

## Sandbox execution

The test runner and sandbox interfaces separate generated-project execution from the orchestration host. Production deployment must back these interfaces with a genuinely isolated execution environment such as restricted containers or another hardened sandbox.

Required production controls include filesystem isolation, resource/process limits, execution timeouts, bounded output, network restrictions where appropriate, secret isolation, and audit logging. A fake/test sandbox backend is suitable only for tests and must not be mistaken for production isolation.

## Performance controls

Phase 17 adds conservative runtime primitives for bounded parallel work, a small TTL/LRU cache, and performance counters. These controls are designed to reduce duplicate work and uncontrolled concurrency without weakening dependency, security, or correctness guarantees.

Optimization should be measurement-driven. Do not increase parallel agent execution beyond provider, sandbox, memory, or project-file ownership limits merely to improve apparent throughput.

## Logging and observability

Log useful structured events such as task/agent lifecycle changes, provider failures, file changes, builds, tests, repairs, security warnings, and project completion. Sanitize exceptions and never log passwords, API keys, bearer tokens, authorization headers, or other credentials.

## Development rules

Before modifying an existing subsystem, inspect the current implementation and its tests. Keep API contracts and agent schemas explicit, prefer the smallest reliable fix, preserve working behavior, and add tests for meaningful behavior changes.

Architecture conflicts should be escalated to the orchestrator/architect instead of being silently resolved by an implementation agent.

## Roadmap

- Phases 1–17: platform architecture and implementation foundation
- Phase 18: documentation and developer experience
- Phase 19: final production review, end-to-end validation, release-readiness report, and remaining-risk inventory

The project is not considered production-ready solely because all implementation phases exist. Phase 19 must verify the actual repository state, CI, configuration, security boundaries, integration behavior, and deployment assumptions before a production release is declared.
