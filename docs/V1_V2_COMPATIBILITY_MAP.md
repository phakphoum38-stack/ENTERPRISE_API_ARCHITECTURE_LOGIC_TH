# V1/V2 Compatibility Map

Baseline: `main` @ `a06f0b7`

## Compatibility policy

V1 remains supported for existing clients. V2 adds versioned orchestration, agent, workspace, knowledge, readiness and developer surfaces without silently changing the V1 contract. V3 runtime is the canonical execution owner; it does not justify deleting V1/V2 transport modules.

| Surface | V1 contract/owner | V2 contract/owner | V3 relationship | Lifecycle | Retirement condition |
|---|---|---|---|---|---|
| Provider listing and AI generation | `/v1/providers`, `/v1/ai/generate`; `server.py` | Reused through shared provider adapters | V3 provider registry/resilience is canonical runtime owner | compatibility / active | Versioned replacement plus client migration and release evidence |
| Conversation analysis and knowledge preview | `/v1/conversations/analyze`; `server.py` | Workspace/knowledge APIs | V3 evidence and artifact boundaries remain canonical | compatibility / active | V2/V3 artifact workflow covers all clients and migration is documented |
| Knowledge artifacts and graph | `/v1/knowledge/artifacts`, `/v1/knowledge/graph`; curator/knowledge ops | `/v2/workspaces/{workspace_id}/knowledge`; `v2_server.py` | V3 evidence/artifact modules own execution outputs | compatibility / active | Provenance-preserving replacement, export/import test and client migration |
| Agent catalog/readiness/discovery | `/v1/agents*`; `agent_server.py` | `/v2/agents*`; shared dynamic registry | V3 agent/provider runtime owns execution | compatibility / active | V3 transport contract, client migration and exact-SHA evidence |
| Orchestration create/history/actions | `/v1/agents/orchestrations*`; `agent_orchestrator.py` | `/v2/orchestrations*`; `v2_server.py` | V3 queue/runner/tracker own execution lifecycle | compatibility / active | V3 API contract supersedes transport, with retry/cancel/audit parity |
| Readiness and diagnostics | `/health` and V1 readiness behavior | `/v2/health/readiness`, V2 observability | V3 runtime health/evidence remains source of truth | active | Replacement exposes equivalent signals and release gate consumes it |
| Developer identity/access | V1-compatible auth/session helpers | `/v2/developer/*`; developer server modules | V3 runtime must receive verified identity context | compatibility / active | New versioned identity contract and migration of all clients |
| Google identity and Workspace | `/v1/auth/google/*`, `/v1/google-workspace/*` | No separate V2 namespace currently | Adapter boundary remains outside V3 execution core | active | Versioned replacement with OAuth redirect and scope migration evidence |
| Local storage and user isolation | Shared V1 local-first storage and sessions | V2 workspace and durable orchestration storage | V3 user context and durable runtime are canonical owners | compatibility / active | Data migration, rollback, isolation and recovery evidence |

## Current verification

- V2 implementation and OpenAPI alignment tests are present.
- V1 orchestration/agent compatibility tests are present.
- V3 runtime tests cover queue lease, heartbeat, recovery, worker pool and DLQ behavior.
- Research OS API suite covers V1/V2 transport behavior.
- No V1/V2 surface is approved for deletion by this map alone.

## Open migration work

- Repeat all exact-SHA gates for `2.0.0-rc.1` from `V2_FAST_TRACK.md`.
- Define and publish a versioned V3 API contract before changing transport ownership.
- Record client-by-client migration status for Flutter, web, developer and Owner Special surfaces.
- Preserve rollback and data-export paths before any compatibility retirement.

## Retirement rule

A V1/V2 component may be retired only after an explicit replacement, migration path, compatibility tests, rollback/data preservation evidence and owner approval are recorded on the release commit.
