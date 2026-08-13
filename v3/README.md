# Research OS V3 — Full System

Research OS V3 is the local-first full-system line with one coordination authority: `UnifiedMasterOrchestrator`.

## Current capability state

- Adaptive logical hierarchy: `3^1`, `3^3`, `6^3`, `3^6`, `6^6`, `10^10`.
- `10^10` is a planning ceiling, not a live worker count.
- Unified skill registry: 40 capabilities.
- Native execution paths: 40.
- Context-only adapters: 0.
- Owner/Friend source is restored under `owner_special/research_os_friend/` for provenance and compatibility; its orchestrator is not started.
- Migrated capability lines execute only through `NativeSkillRuntime` under the V3 master.
- Five governed tools are registered, including Drive package discovery and Drive package invocation.
- Five on-demand role agents remain under the same master.

## Native skill contract

Each skill exposes origin, capability, runtime mode, source, and execution adapter. Existing V3 implementations use `v3-core`; migrated V1/V2, Owner/Friend, and legacy implementations use `v3-adapter`.

`POST /v3/skills/execute` is the explicit execution boundary. Actions that can change persisted state require per-request approval. A model response is not evidence that an action ran; an explicit runtime result is required.

## Drive Tool Runtime Adapter

Google Drive remains storage. `DriveToolRuntimeAdapter` consumes tool packages from a locally synchronized Drive root configured by `RESEARCH_OS_DRIVE_TOOL_ROOT`. Packages are checked for path containment and SHA-256 integrity before a supported runtime is invoked. Shell invocation is disabled and runtime duration/output are bounded.

Registered Drive tools:

- `drive-tools-list` — read-only discovery.
- `drive-tool-execute` — approval required.

## API

Read/status: `/health`, `/v3/master`, `/v3/factory/plan`, `/v3/providers`, `/v3/skills`, `/v3/tools`, `/v3/agents`, `/v3/user`, `/v3/memory`.

Governed operations: `/v3/chat`, `/v3/memory`, `/v3/agents/run`, `/v3/skills/execute`, `/v3/tools/execute`.

## Validation

Local Python validation for this source set: **120 passed, 1 skipped, 7 subtests passed**. Service Smoke confirms 40 native skills, 0 context-only adapters, 5 tools, 5 agents, Drive runtime availability, Chat/Memory flow, user isolation, and the `10^10` logical ceiling.

Flutter validation and Windows Candidate validation are still required on the exact final GitHub SHA before PR #41 is marked Ready or merged.
