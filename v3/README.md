# Research OS V3.2 — Unified Full System 10x10

Research OS V3.2 is the local-first unified line with one coordination authority: `UnifiedMasterOrchestrator`.

## Current capability state

- Adaptive logical hierarchy: `1^3`, `3^1`, `3^3`, `6^3`, `3^6`, `6^6`, `10^10`.
- `10^10` is a logical planning ceiling, not a live worker count.
- The Brain selects the smallest profile that satisfies the workload; real execution stays bounded.
- Unified skills, governed tools, role agents, durable memory, provider routing, factory planning, and Drive runtime adapters share the same V3 authority.
- Owner/Friend source remains available for provenance and compatibility without creating a competing control plane.
- V3.2 preserves the chat contract `research-os-v3-chat-v1` and accepts `message` plus legacy aliases `text`, `prompt`, and `question`.
- Provider secrets stay outside Flutter responses, status contracts, audit records, and evidence.

## API surface

Read/status endpoints:

- `/health`
- `/v3/master`
- `/v3/factory/plan`
- `/v3/providers`
- `/v3/skills`
- `/v3/tools`
- `/v3/agents`
- `/v3/user`
- `/v3/memory`

Governed operation endpoints:

- `/v3/chat`
- `/v3/memory`
- `/v3/agents/run`
- `/v3/skills/execute`
- `/v3/tools/execute`

Write-capable operations fail closed unless their approval boundary is satisfied.

## Desktop and Windows line

The V3.2 Flutter surface exposes Home, Chat, Agents, Memory, Skills, Tools, Factory, and Providers. The Windows package keeps the service loopback-only on `127.0.0.1:8788`, preserves local data under `ProgramData\\ResearchOSV3`, and retains the installed-EXE startup proof for `/health`, `/v3/user`, `/v3/providers`, and `/v3/chat`.

## Validation rule

Source, Flutter, service, installer, installed executable, upgrade, uninstall, and evidence gates are validated from the exact candidate revision. A capability or action is never considered executed merely because a model says it ran; explicit runtime or validation evidence is required.
