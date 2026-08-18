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

- [ ] OpenAPI endpoint ↔ implementation matrix
- [ ] Tool registry with lifecycle state
- [ ] Workflow/GitHub Actions deduplication matrix
- [ ] V1/V2 compatibility map
- [ ] V3 API contract draft
- [ ] Durable queue / lease / heartbeat implementation gap analysis
- [ ] Authentication and secret boundary audit
- [ ] Observability / metrics / tracing coverage
- [ ] Release artifact and installer contract alignment
- [ ] Delete/retire candidates list with evidence

## Rule

No deletion is allowed solely because a component looks old. A component is retired only after an explicit replacement, migration path, test coverage, and release evidence exist.
