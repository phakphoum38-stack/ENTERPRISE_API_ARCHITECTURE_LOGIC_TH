# Autobot Mission Control Phase 4H — Unified Read-Only Snapshot Task

## Objective
Unify the validated Mission Control projections into one bounded, owner-scoped, deterministic snapshot suitable for the future desktop UI.

## Composition
Combine only validated projections:
- Trace (4A)
- Timeline (4B)
- Capability/Health (4C)
- UI Schema (4D)
- Evidence/Provenance (4E)
- Gate Status (4G)

Build Identity (4F) may be included only from canonical evidence and must remain presentation-only.

## Required invariants
- One snapshot schema/version with explicit bounds and truncation.
- `read_only=true` throughout.
- Exact owner scope; fail closed on mismatch.
- Deterministic ordering.
- No duplicate execution/health/evidence/approval/policy systems.
- No status fabrication, authority escalation, or implicit approval.
- Preserve exact source identifiers and provenance.
- Reject dynamic/executable/mutation/secret-like payloads.
- UI consumes the snapshot; the snapshot does not execute anything.

## Safety
No execution, workflow dispatch, build/install/release operations, network side effects, persistence mutation, authorization, approval, policy, skill, registration, MCP, browser, Computer Use, or OS-input authority.

## Tests / evidence
Cover composition, owner isolation, schema compatibility, bounds, truncation, deterministic output, conflicting source data, malformed evidence, secret redaction, and input immutability. Produce a clean first-class `.diff` artifact and machine-readable evidence.

## Workflow discipline
Do not manually dispatch workflows. Do not merge from this task. Record exact lineage and authoritative verification results.
