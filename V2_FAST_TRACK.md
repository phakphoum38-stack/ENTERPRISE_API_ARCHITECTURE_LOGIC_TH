# Research OS v2 Fast-Track Plan

Status: PLANNING — V2

Baseline target: Research OS `1.0.0` stable.
Development branch: `develop/v2`.

## V2 principles

- Preserve V1 compatibility unless a migration is explicitly documented.
- Keep one source of truth for runtime, API contracts, orchestration state, and release evidence.
- Prefer local-first operation and make cloud/provider dependencies optional.
- Every write-capable agent action must remain auditable and confirmation-aware.
- New V2 capabilities must ship with tests and observable health signals.

## Phase 1 — Durable orchestration

- [ ] Persist orchestration runs and step state across restarts
- [ ] Resume interrupted orchestration safely
- [ ] Run history, filtering, and searchable audit timeline
- [ ] Retry policy with bounded retries and explicit failure states
- [ ] Cancellation support for queued/runnable work
- [ ] API contract and migration tests for durable runs

## Phase 2 — Dynamic Agent Platform

- [ ] Dynamic agent registration and capability discovery
- [ ] Agent health/readiness status
- [ ] Capability-based routing with explainable selection
- [ ] Provider/model preferences per agent without hard dependency on one vendor
- [ ] Fallback routing when a provider or agent is unavailable
- [ ] Permission profiles for read/write/network-sensitive capabilities

## Phase 3 — Workspace and Knowledge Engine

- [ ] Workspace/project boundary for context and artifacts
- [ ] Local knowledge index with incremental updates
- [ ] Search across Research Artifacts, documents, and orchestration history
- [ ] Provenance/evidence links for generated outputs
- [ ] Duplicate/conflict detection for knowledge records
- [ ] Export/import of workspace metadata without losing provenance

## Phase 4 — Agent Center V2 UI

- [ ] Visual orchestration graph and dependency status
- [ ] Live run timeline and per-step logs
- [ ] Approval inbox for write-capable actions
- [ ] Retry/cancel/resume controls
- [ ] Agent health and capability dashboard
- [ ] Workspace selector and knowledge search UI
- [ ] Accessibility and widget/integration tests for critical flows

## Phase 5 — API V2 and compatibility

- [ ] Define V2 API namespace/contract without breaking required V1 clients
- [ ] Versioned schemas for orchestration, agents, workspaces, and evidence
- [ ] Compatibility tests covering supported V1 endpoints
- [ ] Deterministic error model and machine-readable error codes
- [ ] Pagination/filtering contracts for run history and knowledge queries
- [ ] OpenAPI contract tests

## Phase 6 — Observability and operations

- [ ] Structured runtime logs with correlation/run IDs
- [ ] Health/readiness checks for runtime, agents, provider adapters, and storage
- [ ] Local diagnostics bundle with secrets redacted
- [ ] Performance baseline for startup, orchestration latency, and memory use
- [ ] Failure-injection tests for provider/storage/runtime interruptions
- [ ] Production health coverage for new V2 services/endpoints

## Phase 7 — Desktop delivery V2

- [ ] V2 Windows release build and installer validation
- [ ] Upgrade path from V1 preserving local data/configuration
- [ ] Rollback path to last stable V1 baseline where compatible
- [ ] Release manifest with component versions and artifact digests
- [ ] Same-target-SHA end-to-end candidate pipeline
- [ ] Reproducible verified release artifact

## Quality gates

- [ ] Flutter analyze clean
- [ ] Flutter/widget/integration tests pass
- [ ] Agent Platform tests pass
- [ ] API contract/compatibility tests pass
- [ ] Persistence/migration tests pass
- [ ] Windows release build pass
- [ ] Upgrade/rollback installer tests pass
- [ ] Release artifact verification pass
- [ ] Production Health pass
- [ ] Full V2 candidate pipeline passes on one target SHA

## Version sequence

1. `2.0.0-dev.1` — first integrated V2 development candidate
2. `2.0.0-rc.1` — full regression/release candidate
3. `2.0.0` — stable after upgrade, rollback, release, and health gates pass

## Working rule

Implement V2 as vertical slices. Before creating a new subsystem, inspect the existing V1 implementation and extend it when it already owns the responsibility. Do not duplicate runtime, API, storage, release, or orchestration sources of truth.
