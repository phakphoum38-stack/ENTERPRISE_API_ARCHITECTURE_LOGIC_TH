# Research OS H13 — Learned-Skill Activation Boundary

## Purpose

H13 defines the boundary between a governed learned-skill consumption decision and any later runtime activation.

Flow:

`H12 CONSUMPTION DECISION → ACTIVATION REQUEST → IDENTITY + DECISION CHECK → APPROVAL CHECK → ACTIVATION SNAPSHOT`

The activation contract does **not** execute a skill. It proves that a later executor may receive an activation intent only after the required identity and approval conditions are satisfied.

## Invariants

- Owner, source SHA, correlation ID, and skill fingerprint MUST match the registry entry.
- The activation request MUST reference an H12 decision for the same identity.
- `inspect` activation remains read-only and requires no approval.
- `execute` activation MUST require an explicit approved decision; otherwise the result is `REQUIRE_APPROVAL` or `DENY`.
- H13 MUST NOT call an executor, shell, process, MCP tool, browser, Computer Use, GitHub mutation, workflow dispatch, installer, merge, release, or ref mutation.
- Approval authority remains in `ApprovalGate`; H13 only consumes an externally supplied approval result.
- Secret-like, credential-like, executable, dynamic, authority, release, or bypass content MUST fail closed.
- Snapshots MUST be bounded, detached, deterministic, and read-only.

## Result model

Allowed decisions:

- `ALLOW_INSPECTION`
- `REQUIRE_APPROVAL`
- `ALLOW_ACTIVATION`
- `DENY`

`ALLOW_ACTIVATION` means only that the governed activation boundary has been satisfied. It is **not** an execution, release, merge, install, or approval authority.

## Evidence

The implementation and tests are the authoritative artifacts. CI generates the actual evidence for this phase; no manual evidence or SHA is fabricated by H13.
