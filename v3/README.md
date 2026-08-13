# Research OS V3 Full System

Research OS V3 is the unified local-first runtime and workspace. The system keeps one coordination authority while exposing Chat, Memory, Skills, Tools, Agents, Providers, Software Factory, evidence, and user isolation through one V3 service boundary.

## Core rules

- One `UnifiedMasterOrchestrator` is the coordination authority.
- Brain capacity is adaptive and lazy. Logical capacity is never interpreted as a request to pre-spawn workers.
- Scale profiles are `3^1`, `3^3`, `6^3`, `3^6`, `6^6`, and `10^10`.
- `10^10 = 10,000,000,000` is the maximum logical planning ceiling; real execution remains bounded by explicit concurrency limits and queue/backpressure.
- Provider secrets stay outside Flutter and are never returned by status contracts.
- Existing `RESEARCH_OS_OPENAI_API_KEY` or `OPENAI_API_KEY` can be used by the installed service; OpenAI-compatible execution is preferred when ready and mock remains an offline fallback.
- Mutable data is user/profile isolated under the V3 data root.
- Write-capable tools fail closed unless explicit approval is supplied.
- Software Factory execution remains deterministic: Master -> Factory -> Team -> Tests -> Release.
- Evidence is incremental; later failures cannot erase earlier passed evidence.

## Native V3 capability layers

- `research_os_v3/brain.py` — adaptive scale selection.
- `research_os_v3/orchestrator.py` — Unified Master composition and Chat/Tool execution entrypoints.
- `research_os_v3/providers.py` — secret-safe provider adapters, retry, circuit breaker, and fallback.
- `research_os_v3/skills.py` — V1/V2/V3 skills represented as native V3 capabilities with provenance.
- `research_os_v3/tools.py` — governed tool registry with read/write risk and approval metadata.
- `research_os_v3/agents.py` — role-based agents activated on demand rather than permanently running workers.
- `research_os_v3/memory.py` — explicit durable per-user memory and deterministic local retrieval.
- `research_os_v3/factory.py` / `execution.py` — bounded Software Factory planning and execution.
- `research_os_v3/service.py` — loopback-only Full System API.
- `flutter_app/` — Home, Chat, Agents, Memory, Skills, Tools, Factory, and Providers workspaces.

## Full System API

Read contracts:

- `GET /health`
- `GET /v3/master`
- `GET /v3/factory/plan`
- `GET /v3/providers`
- `GET /v3/skills`
- `GET /v3/tools`
- `GET /v3/agents`
- `GET /v3/user`
- `GET /v3/memory`

Governed execution:

- `POST /v3/chat`
- `POST /v3/memory`
- `POST /v3/agents/run`
- `POST /v3/tools/execute`

User-owned endpoints require `X-Research-OS-User` and optional `X-Research-OS-Profile`. Write tools that require approval additionally require `X-Research-OS-Approval: granted`.

## Validation

The V3 test suite covers adaptive 10^10 selection, backpressure above the maximum ceiling, provider secret redaction, user/profile isolation, durable memory retrieval, Skills/Tools/Agents catalogs, approval gating, Chat/Agent execution, Software Factory determinism, and local API end-to-end behavior.
