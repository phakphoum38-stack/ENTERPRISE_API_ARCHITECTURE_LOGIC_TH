# Research OS H14 — Executor Handoff Boundary

## Purpose

H14 defines the final handoff contract between an approved learned-skill activation intent and a future executor.

Flow:

`H13 ACTIVATION → HANDOFF REQUEST → IDENTITY CHECK → EXECUTOR CAPABILITY CHECK → HANDOFF SNAPSHOT`

H14 does not execute the request. It produces a bounded handoff object that a separately governed executor may consume.

## Invariants

- Owner, source SHA, correlation ID, and skill fingerprint MUST match the H13 activation context.
- Only `ALLOW_ACTIVATION` may produce an execution handoff.
- `ALLOW_INSPECTION` MUST never become an execution handoff.
- Executor capability MUST be explicitly declared and allowlisted.
- Unsupported capabilities fail closed.
- H14 has no executor, approval, release, merge, install, dispatch, ref-mutation, or evidence-fabrication authority.
- H14 MUST reject secret-like, credential-like, executable, dynamic, authority-like, and bypass content.
- Handoff snapshots are bounded, deterministic, detached, and read-only.

## Allowed executor capabilities

The contract initially permits only declarative capability names:

- `LEARNED_SKILL_EXECUTOR`
- `LEARNED_SKILL_INSPECTOR`

The capability name is a declaration, not an invocation.

## Boundary meaning

`HANDOFF_READY` means the handoff contract is internally satisfied. It does not mean that an executor has run, that an external side effect occurred, or that a release/approval was granted.

CI remains authoritative for implementation correctness and generated evidence.
