# Research OS v2 Fast-Track Plan

Status: RELEASE CANDIDATE — `2.0.0-rc.1`; exact-SHA regression, installer validation, verified candidate, and live staging revalidation are in progress.

Baseline target: Research OS `1.0.0` stable (`d05189d151b6bfa65938dad7a812ac104db195f4`).
Release-candidate branch: `release/v2.0.0-rc.1`.

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

- [x] Visual orchestration graph and dependency status
- [x] Live run timeline and per-step audit events
- [x] Approval inbox for write-capable actions
- [x] Retry/cancel/resume controls
- [x] Agent health and capability dashboard
- [x] Workspace selector and knowledge search UI backed by the existing local Workspace Knowledge Engine
- [x] Accessibility semantics and widget/integration tests for critical flows

## Phase 5 — API V2 and compatibility

- [x] Define V2 API namespace/contract without breaking required V1 clients
- [x] Versioned schemas for orchestration, agents, workspaces, evidence, readiness, and errors
- [x] Compatibility tests covering supported V1 orchestration/agent endpoints
- [x] Deterministic error model and machine-readable error codes
- [x] Pagination/filtering contracts for run history and workspace knowledge queries
- [x] OpenAPI contract tests for the declared V1/V2 contract

## Phase 6 — Observability and operations

- [x] Structured runtime events with correlation/run IDs propagated across task lifecycle
- [x] Health/readiness checks for runtime, agents, provider adapters, and storage
- [x] Local diagnostics bundle with secrets redacted
- [x] Performance baseline for startup, readiness, orchestration latency, and memory RSS enforced by the V2 quality probe
- [x] Failure-injection tests for transient provider failure, non-retryable provider failure, storage denial, and runtime interruption/resume
- [x] Production health coverage for new V2 readiness endpoint

## Phase 7 — Desktop delivery V2

- [x] V2 Windows release build and installer validation passed on verified development candidate
- [x] Upgrade path from V1 preserving local data/configuration passed under CI-controlled service quiesce
- [x] Rollback path to last stable V1 baseline validated
- [x] Release manifest with component versions and artifact digests
- [x] Same-target-SHA end-to-end candidate pipeline passed on verified development candidate
- [x] Reproducible verified candidate artifact produced
- [x] Live Render staging health/readiness and Developer security boundary passed on verified development candidate
- [ ] Repeat all exact-SHA gates for `2.0.0-rc.1`

## Quality gates for 2.0.0-rc.1

- [ ] Agent Platform
- [ ] Developer Platform
- [ ] Build Service Host
- [ ] Branding
- [ ] Build Windows App
- [ ] Runtime Smoke
- [ ] Build Installer
- [ ] Installer Validation
- [ ] Windows Desktop verified candidate
- [ ] Live Render staging gate

## V2 Completion Crew

Fresh V2-only helpers are registered separately from the six core agents and do not fall back to or replace them:

- `v2_workspace_engineer` — Phase 3 Workspace/Knowledge
- `v2_agent_center_engineer` — Phase 4 Agent Center UI
- `v2_api_compat_engineer` — Phase 5 API compatibility
- `v2_reliability_release_engineer` — Phase 6–7 reliability/release

## Version sequence

1. `2.0.0-dev.1` — integrated V2 development candidate, fully verified including live staging
2. `2.0.0-rc.1` — current full regression/release candidate
3. `2.0.0` — stable only after RC exact-SHA gates, staging validation, and explicit merge approval

## Publication hold

Do not merge `main`, create a GitHub Release/tag, publish a public announcement, or deploy V2 over production V1 without explicit owner approval.

## Working rule

Implement V2 as vertical slices. Before creating a new subsystem, inspect the existing V1 implementation and extend it when it already owns the responsibility. Do not duplicate runtime, API, storage, release, or orchestration sources of truth.
