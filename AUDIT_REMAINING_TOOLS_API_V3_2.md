# V3.2 Remaining Tools / Features / API Audit

Status: Audit baseline
Baseline: `main` @ `e57f92acddf90de5e0c37009d9d7fb2bdf92948b`

## Purpose

Inventory capabilities that still exist outside the V3.2 active runtime contracts so they can be classified as:

1. **Keep** — still required and supported.
2. **Promote** — useful capability that should become an explicit V3.2/V3.x contract.
3. **Compatibility** — retained for V1/V2 compatibility and must not be deleted casually.
4. **Retire** — obsolete duplicate or superseded implementation.
5. **Verify** — present in the tree but requires runtime evidence before being declared production-ready.

## Findings

### 1. Version metadata drift — PROMOTE / FIX

`VERSION_INDEX.md` still advertises `v1.0.0-draft` as the active development version even though V3.2 workflow-runtime contracts are active on `main`.

Action: align the central version index with the actual released/active V3.2 state and preserve the historical V1 snapshot.

### 2. Research OS OpenAPI contract — VERIFY / PROMOTE

`tools/research_os_api/openapi.yaml` declares `2.0.0-rc.1` and `x-research-os-v2-status: draft` while the repository now contains V3 runtime, agent, orchestration, workspace, evidence, and workflow-runtime capabilities.

Action: perform endpoint-to-implementation coverage audit. Do not change the API version merely to make metadata look current. Promote only endpoints proven by implementation and E2E evidence.

### 3. V2 API implementation — COMPATIBILITY / VERIFY

The repository contains V2 server, completion crew, observability, quality gate, and related tests. These should be treated as compatibility/runtime assets until a V3 API contract explicitly supersedes them.

Action: map each V2 endpoint/module to V3 owner, migration status, and retirement criteria.

### 4. V3 runtime — KEEP

The V3 tree already contains queue, runner, resilience, work tracker, status service, research execution/planning, evidence, provider, transport, and user-context modules plus E2E tests.

Action: use these as the canonical owners; do not create parallel runtime implementations under `tools/` merely to replace working V3 components.

### 5. Workflow Runtime Foundation — KEEP / PROMOTE

`current/workflow-runtime/` now contains active V3.2 contracts for schema, state machine, events, and retry policy.

Action: next maturity layer should be implementation coverage: durable queue, lease/ack, heartbeat, worker pool, dead-letter handling, and event delivery, each backed by tests before promotion.

### 6. Tooling inventory — VERIFY

Existing tool families include file audit, house command, research curator, Research OS API, service host, V3 scripts, and multiple GitHub Actions gates.

Action: produce a tool registry with owner, input/output contract, runtime dependency, authentication requirement, evidence test, and lifecycle status.

### 7. GitHub Actions — VERIFY / CONSOLIDATE

There are multiple V3, Research OS, candidate, artifact, provider, Windows, iOS, and owner-special workflows.

Action: identify overlapping gates and define one canonical release gate. Keep specialized workflows where they protect a distinct artifact/platform; retire duplicate checks only after equivalent coverage is proven.

### 8. Applications / adapters — VERIFY

Flutter, web, developer, owner-special, signing, Windows service, and API clients are present.

Action: map every application surface to the canonical V3 API and workflow-runtime contract. Flag clients that still target V1/V2-only endpoints.

## Proposed next audit passes

- [x] OpenAPI endpoint ↔ implementation matrix — see `docs/API_IMPLEMENTATION_MATRIX.md`; added route groups remain draft-level pending release evidence.
- [x] Tool registry with lifecycle state — see `docs/TOOL_REGISTRY.md`; platform/deployment evidence remains open for `verify` tools.
- [x] Workflow/GitHub Actions deduplication matrix — see `docs/WORKFLOW_DEDUPLICATION_MATRIX.md`; consolidation candidates require equivalent-coverage proof.
- [x] V1/V2 compatibility map — see `docs/V1_V2_COMPATIBILITY_MAP.md`; retirement remains blocked until replacement, migration and release evidence exist.
- [x] V3 API contract draft — see `docs/V3_API_CONTRACT_DRAFT.md`; promotion still requires client migration, schema completion and exact-SHA evidence.
- [x] Durable queue / lease / heartbeat implementation gap analysis — see `docs/DURABLE_RUNTIME_GAP_ANALYSIS.md`; durable event store and queue-to-engine projection remain implementation gaps.
- [x] Authentication and secret boundary audit — see `docs/AUTH_SECRET_BOUNDARY_AUDIT.md`; production secret-store and deployment evidence remain open.
- [x] Observability / metrics / tracing coverage — see `docs/OBSERVABILITY_COVERAGE.md`; production metrics, tracing export and alert evidence remain open.
- [x] Release artifact and installer contract alignment — see `docs/RELEASE_ARTIFACT_INSTALLER_ALIGNMENT.md`; Windows candidate, installer and exact-SHA evidence remain open.
- [x] Delete/retire candidates list with evidence — see `docs/DELETE_RETIRE_CANDIDATES.md`; zero deletion candidates are approved until replacement and release evidence exist.

## Validation snapshot

Validated on `main` @ `a06f0b7`:

- V3 runtime and hardening tests: `144 tests OK` (`1 skipped`)
- Research OS API tests: `114 tests OK`
- Worker crash recovery evidence confirmed lease reclaim and stale-ack rejection.
- Generated runtime test artifacts were removed after validation; intentional source/document changes remain uncommitted.

This snapshot confirms the current testable implementation baseline. It does not close the remaining audit passes or replace exact-SHA release-gate evidence.

## Rule

No deletion is allowed solely because a component looks old. A component is retired only after an explicit replacement, migration path, test coverage, and release evidence exist.
