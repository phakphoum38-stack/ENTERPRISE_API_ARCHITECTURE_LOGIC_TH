# Research OS H12 — Governed Learned-Skill Consumption Boundary

## Purpose

H12 defines the boundary between a verified learned-skill registry entry and any future runtime consumer. Registry state may be inspected, but learned procedures are never executed implicitly.

## Contract

`REGISTRY ENTRY → CONSUMPTION REQUEST → IDENTITY CHECK → INTENT DECISION → SNAPSHOT`

## Invariants

- Owner, source SHA, and correlation ID must match the registered entry.
- Lookup is deterministic and bounded.
- Inspection is read-only.
- Execution intent is explicit and never becomes execution authority.
- Any future side-effecting execution requires the existing approval/execution boundary outside this contract.
- Unknown or mismatched entries fail closed.
- Secret-like, executable, dynamic, approval, release, or authority content is rejected.
- Returned snapshots are detached from internal registry state.
- H12 has no execution, approval, release, install, workflow-dispatch, Git-ref, merge, or evidence-fabrication authority.

## Safety boundary

H12 does not run learned procedures. It only determines whether a registered learned skill may be inspected and emits a bounded consumption decision. CI remains authoritative for repository verification.
