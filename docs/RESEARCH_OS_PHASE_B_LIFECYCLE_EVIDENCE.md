# Research OS Phase B — Lifecycle Evidence

Phase B closes the evidence-binding gap without introducing another runtime.

## Canonical flow

```text
Command
  → Authorization
  → Existing Executor
  → Observation
  → Evidence
  → State
  → Recovery
```

The lifecycle is:

`INTENT → VALIDATE → PREPARE → AUTHORIZE → EXECUTE → OBSERVE → EVIDENCE → COMPLETE/RECOVER`

## Invariants

- The existing executor remains execution authority.
- Authorization is not granted by the evidence ledger.
- Every evidence event carries `event_id`, `correlation_id`, `source_sha`, `target_sha`, `workflow_run_id`, `contract_version`, and `fingerprint`.
- Evidence is append-only JSONL.
- A source-SHA mismatch fails closed.
- A recovery state requires an explicit recovery reason.
- A lifecycle cannot validate unless it reaches `COMPLETE` or `RECOVER`.
- Assurance records evidence; it does not execute capabilities.
- Final Gate remains release authority.

## Scope

This phase provides the reusable lifecycle/evidence boundary. It does not yet dispatch commands into Friend, Agent, GitHub, or Factory. Those adapters remain responsible for invoking their existing executors and projecting their observations into this contract.

That separation prevents Phase B from becoming a second runtime or command bus.
