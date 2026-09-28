# Research OS Final Gate Evidence

## Purpose

Bind one workflow lifecycle to one immutable canonical identity before Final Gate evaluation.

The evidence identity is:

`workflow_id -> run_id -> execution_id -> delivery_ids -> resource_versions -> terminal_status -> canonical_sha256`

## Contract

- Canonical SHA uses deterministic JSON serialization.
- Workflow, run, and execution identity must match the expected Final Gate target.
- Delivery IDs and resource versions remain explicit lineage inputs.
- Identity mismatch fails closed.
- The governed runtime exposes the evidence builder without introducing another queue, event bus, or evidence store.

## Flutter validation

The previously deferred Developer Access / Flutter Code Tool validation is now part of the normal Flutter quality gate. Windows release builds also bind the Research OS Flutter client to the packaged local API at `http://127.0.0.1:8787`; public iOS/web builds may continue to supply their own `RESEARCH_OS_API_BASE_URL`.
