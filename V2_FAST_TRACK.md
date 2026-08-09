# Research OS v2 Fast-Track Plan

Status: IMPLEMENTING — `2.0.0-dev.1` candidate; Phase 7 validation and final quality gates pending.

Baseline target: Research OS `1.0.0` stable (`d05189d151b6bfa65938dad7a812ac104db195f4`).
Development branch: `develop/v2`.

## V2 principles

- Preserve V1 compatibility unless a migration is explicitly documented.
- Keep one source of truth for runtime, API contracts, orchestration state, and release evidence.
- Prefer local-first operation and make cloud/provider dependencies optional.
- Every write-capable agent action must remain auditable and confirmation-aware.
- New V2 capabilities must ship with tests and observable health signals.

## Phase 1 — Durable orchestration

- [x] Persist orchestration runs and step state across restarts
- [x] Resume interrupted orchestration safely
- [x] Run history, filtering, and searchable audit timeline
- [x] Retry policy with bounded retries and explicit failure states
- [x] Cancellation support for queued/runnable work
- [x] API contract and migration tests for durable runs

## Phase 2 — Dynamic Agent Platform

- [x] Dynamic agent registration and capability discovery
- [x] Agent health/readiness status
- [x] Capability-based routing with explainable selection
- [x] Provider/model preferences per agent without hard dependency on one vendor
- [x] Fallback routing when a provider or agent is unavailable
- [x] Permission profiles for read/write/network-sensitive capabilities

## Phase 3 — Workspace and Knowledge Engine

- [x] Workspace/project boundary for context and artifacts
- [x] Local knowledge index with incremental updates
- [x] Search across Research Artifacts, documents, and orchestration history
- [x] Provenance/evidence links for generated outputs
- [x] Duplicate/conflict detection for knowledge records
- [x] Export/import of workspace metadata without losing provenance

## Phase 4 — Agent Center V2 UI

- [ ] Visual orchestration graph and dependency status — dependency status is implemented; graphical graph view remains
- [x] Live run timeline and per-step audit events
- [x] Approval inbox for write-capable actions
- [x] Retry/cancel/resume controls
- [x] Agent health and capability dashboard
- [ ] Workspace selector and knowledge search UI — workspace selector is implemented; knowledge-search UI remains
- [ ] Accessibility and widget/integration tests for critical flows — widget tests added; explicit accessibility gate remains

## Phase 5 — API V2 and compatibility

- [x] Define V2 API namespace/contract without breaking required V1 clients
- [ ] Versioned schemas for orchestration, agents, workspaces, and evidence — orchestration/agents/readiness/error schemas implemented; workspace/evidence transport schemas remain
- [x] Compatibility tests covering supported V1 orchestration/agent endpoints
- [x] Deterministic error model and machine-readable error codes
- [ ] Pagination/filtering contracts for run history and knowledge queries — run-history cursor pagination implemented; knowledge-query pagination remains
- [x] OpenAPI contract tests

## Phase 6 — Observability and operations

- [ ] Structured runtime logs with correlation/run IDs — structured event primitive exists; runtime-wide integration remains
- [x] Health/readiness checks for runtime, agents, provider adapters, and storage
- [x] Local diagnostics bundle with secrets redacted
- [ ] Performance baseline for startup, orchestration latency, and memory use — V2 readiness latency gate added; complete baseline run remains
- [ ] Failure-injection tests for provider/storage/runtime interruptions — provider and storage injection added; runtime interruption injection remains
- [x] Production health coverage for new V2 readiness endpoint

## Phase 7 — Desktop delivery V2

- [ ] V2 Windows release build and installer validation
- [ ] Upgrade path from V1 preserving local data/configuration — preservation fixture and in-place validation steps implemented; candidate run remains
- [ ] Rollback path to last stable V1 baseline where compatible — stable baseline recorded; end-to-end rollback validation remains
- [x] Release manifest with component versions and artifact digests
- [ ] Same-target-SHA end-to-end candidate pipeline — manifest binding gate implemented; full candidate run remains
- [ ] Reproducible verified release artifact

## Quality gates

- [ ] Flutter analyze clean on final V2 candidate SHA
- [ ] Flutter/widget/integration tests pass on final V2 candidate SHA
- [x] Agent Platform tests pass on the current `2.0.0-dev.1` implementation line
- [ ] API contract/compatibility tests pass on final V2 candidate SHA
- [x] Persistence/migration tests pass in Agent Platform validation
- [ ] Windows release build pass
- [ ] Upgrade/rollback installer tests pass
- [ ] Release artifact verification pass
- [ ] Production Health pass
- [ ] Full V2 candidate pipeline passes on one target SHA

## V2 Completion Crew

Fresh V2-only helpers are registered separately from the six core agents and do not fall back to or replace them:

- `v2_workspace_engineer` — Phase 3 Workspace/Knowledge
- `v2_agent_center_engineer` — Phase 4 Agent Center UI
- `v2_api_compat_engineer` — Phase 5 API compatibility
- `v2_reliability_release_engineer` — Phase 6–7 reliability/release

## Version sequence

1. `2.0.0-dev.1` — current integrated V2 development candidate
2. `2.0.0-rc.1` — full regression/release candidate after remaining Phase 4–7 gaps and quality gates pass
3. `2.0.0` — stable after upgrade, rollback, release, and health gates pass

## Working rule

Implement V2 as vertical slices. Before creating a new subsystem, inspect the existing V1 implementation and extend it when it already owns the responsibility. Do not duplicate runtime, API, storage, release, or orchestration sources of truth.
