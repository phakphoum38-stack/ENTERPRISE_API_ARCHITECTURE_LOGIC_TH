# Research OS V3 — Clean Architecture Workspace

Research OS V3 is the clean rebuild line for the local-first Research OS runtime and Flutter workspace. V3 keeps one coordination authority, bounded lazy execution, loopback-only local APIs, durable user/profile isolation, governed tools, and provider secrets owned by the service layer.

## V3.1 Full System

The current feature line expands the clean V3 shell into a full local workspace with:

- Unified Master Orchestrator
- adaptive hierarchy through `10^10` logical capacity
- Brain, Providers, Factory, Skills, Tools, Agents, and Memory
- loopback V3 local API
- Flutter workspaces for Home, Chat, Agents, Memory, Skills, Tools, Factory, and Providers
- Windows service/installer Candidate gates

`10^10` means a planning ceiling of 10,000,000,000 logical leaf slots. It is never interpreted as ten billion live processes, threads, or agents. Real execution remains bounded and uses queue/backpressure.

## Unified Brain, Skills, and Chat

V3 is the single execution and coordination authority. The V3 `UnifiedSkillRegistry` exposes native V3 capabilities plus preserved V1/V2, Owner/Friend, and legacy capability knowledge through explicit provenance.

- `runtime_mode: native` means the capability has a V3-native executable implementation.
- `runtime_mode: context-adapter` means the capability is represented for routing/reasoning but must not be claimed as executed without an explicit V3 runtime/tool/agent result.
- `/v3/skills` exposes skill origin, capability, runtime mode, source, and the single authority contract.
- General chat and role agents receive this governed capability context.
- Desktop Flutter chat routes through the loopback V3 `POST /v3/chat` endpoint instead of hard-coding the legacy V1/Gemini path.

This preserves older capability knowledge without starting competing brains or orchestrators.

## Local API

Read/status endpoints:

- `GET /health`
- `GET /v3/master`
- `GET /v3/factory/plan`
- `GET /v3/providers`
- `GET /v3/skills`
- `GET /v3/tools`
- `GET /v3/agents`
- `GET /v3/user`
- `GET /v3/memory`

Governed execution endpoints:

- `POST /v3/chat`
- `POST /v3/memory`
- `POST /v3/agents/run`
- `POST /v3/tools/execute`

Write-capable tools fail closed unless the request includes explicit approval through `X-Research-OS-Approval: granted`.

## Provider configuration

The V3 service can reuse an existing OpenAI-compatible credential without placing the secret in Flutter or status contracts:

- `RESEARCH_OS_OPENAI_API_KEY` preferred alias
- `OPENAI_API_KEY` compatibility alias
- `RESEARCH_OS_OPENAI_ENDPOINT` optional endpoint override
- `RESEARCH_OS_OPENAI_MODEL` optional model override

When no real provider is ready, the deterministic local mock provider remains available for offline validation.

## Validation

Run the Python core and full API tests from the repository root with V3 on `PYTHONPATH`, then run `v3/scripts/service_smoke.py`. Flutter tests and Windows Candidate validation should also be run on the exact final SHA before marking a release or PR ready.

The architecture intentionally separates source presence from runtime execution: a preserved legacy skill in the unified registry is not automatically an executable V3 skill unless its runtime mode says `native` or an explicit adapter/tool implementation is invoked through V3 policy.
