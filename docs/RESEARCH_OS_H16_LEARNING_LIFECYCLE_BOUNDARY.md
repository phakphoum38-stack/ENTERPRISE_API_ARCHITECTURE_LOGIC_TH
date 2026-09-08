# Research OS H16 — Learning Lifecycle Boundary

## Purpose

H16 defines the read-only lifecycle state projection that connects governed executor results back to the learning system.

Flow:

`H15 RESULT → LIFECYCLE CLASSIFICATION → LEARNING STATE → SNAPSHOT`

This contract classifies an externally supplied result; it does not promote, persist, execute, approve, release, or mutate a skill.

## States

- `OBSERVED` — a result exists but is not yet successful learning evidence.
- `LEARNED` — a validated successful result can be represented as learning evidence.
- `FAILED` — execution reported failure.
- `BLOCKED` — governance or safety prevented use.
- `REJECTED` — identity or contract validation failed.

`LEARNED` is informational. H10 promotion remains the promotion boundary.

## Invariants

- H15 identity must match the expected handoff identity.
- Only `SUCCEEDED` can classify as `LEARNED`.
- FAILED and BLOCKED outcomes remain preserved and cannot be promoted here.
- Payloads are bounded, detached, deterministic, and sanitized.
- No registry mutation, promotion, approval, executor invocation, workflow dispatch, ref mutation, merge, release, or installation occurs.
- CI generates authoritative evidence; H16 never fabricates evidence.
