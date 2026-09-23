# Research OS — Outstanding Work Plan

Status: ACTIVE  
CI failures: DEFERRED (fix after the functional backlog is written)  
Baseline: `main`

## Execution order

### W01 — Identity and Authorization
- [ ] Complete provider-neutral login UI for Google, Microsoft, and GitHub.
- [ ] Keep provider secrets and access/refresh tokens server-side.
- [ ] Ensure authorization is resolved from the verified Research OS session.
- [ ] Preserve the Owner capability as unrestricted system authority; do not reduce it to resource-scoped grants.
- [ ] Complete account-link/unlink lifecycle after the first end-to-end provider flows.
- [ ] Add end-to-end tests for session issuance, expiry, revocation, and provider isolation.

### W02 — Owner Developer / Flutter Code Tool
- [x] Project and file selection.
- [x] Read source with SHA.
- [x] Edit and preview diff.
- [x] Apply with original-SHA TOCTOU protection.
- [x] Validate with the external Flutter toolchain.
- [x] Roll back on validation failure.
- [x] Capture evidence.
- [ ] Complete integration coverage for rejection, rollback, and stale-SHA cases.
- [ ] Keep `phakphoum38-stack/flutter` as an External Tool; do not merge its source into the main product UI.

### W03 — Workflow Engine
- [ ] Canonical event contract.
- [ ] Durable queue boundary.
- [ ] Stateless runner contract.
- [ ] Horizontal runner scaling.
- [ ] Idempotency key and delivery-attempt handling.
- [ ] Ack/reconcile policy.
- [ ] Runner isolation and failure recovery.
- [ ] Final Gate aggregation from independent workstream result sets.

### W04 — Resource Conflict / Version Lineage
- [ ] Enforce optimistic version/SHA precondition at every mutation boundary.
- [ ] On stale update: REJECT, stop execution, release resources, and ack/reconcile according to delivery policy.
- [ ] Never overwrite another version.
- [ ] Allow alternate versions to branch without mutating the rejected version.
- [ ] Persist conflict evidence and causal lineage.

### W05 — AI / Brain / Code Writer
- [ ] Canonical Brain tool contract.
- [ ] Code Writer planning → generation → diff → validation → evidence lifecycle.
- [ ] Registry for unfinished tools/functions with explicit states.
- [ ] AI chat integration with requested skills/tools and policy checks.
- [ ] Ensure AI execution enters the canonical resource-control boundary rather than bypassing it.

### W06 — Evidence / Audit / Final Gate
- [ ] Canonical SHA and lineage identity in every work result.
- [ ] Immutable evidence record for execution, validation, rejection, rollback, and promotion.
- [ ] Final Gate consumes result sets/values from workstreams while source remains in its owning workspace.
- [ ] Post-merge verification and rebaseline.
- [ ] Fail closed on identity mismatch or missing required evidence.

### W07 — Packaging
- [ ] Define the final single-EXE boundary.
- [ ] Produce one distributable executable without duplicating the External Flutter Tool source.
- [ ] Add build identity, provenance, and smoke verification to the release gate.

## Explicitly deferred

- Current Flutter CI failures in `apps/research_os_flutter/test/developer_access_page_test.dart` and `apps/research_os_flutter/test/flutter_code_tool_page_test.dart`.
- Do not change the functional backlog to accommodate those failures; fix the tests after the outstanding product/runtime work is written.

## Rules

1. Do not duplicate functionality already present on `main`.
2. Source stays in its owning workstream/branch; only validated state, values, and evidence flow to the Final Gate.
3. One causal lineage and one canonical SHA identify a work item.
4. A rejected stale mutation must never overwrite the competing version.
5. Owner authority is full-system and is not constrained by ordinary resource/scope grants.
6. CI is evidence, not a substitute for implementing the runtime contract.
