# Research OS H15 — Executor Result Boundary

## Purpose

H15 defines the fail-closed boundary for accepting a result from a learned-skill executor after H14 handoff.

Flow:

`H14 HANDOFF → EXTERNAL EXECUTION → RESULT ENVELOPE → IDENTITY CHECK → RESULT VALIDATION → SNAPSHOT`

H15 validates and sanitizes a supplied result. It does not invoke or control the executor.

## Invariants

- Owner, source SHA, correlation ID, skill fingerprint, and handoff fingerprint must match the expected handoff.
- Result status is limited to `SUCCEEDED`, `FAILED`, or `BLOCKED`.
- Result payloads are bounded and detached.
- Secret-like, credential-like, executable, dynamic, authority, release, merge, install, dispatch, shell, process, MCP, or Computer Use content fails closed.
- A successful result is evidence of an external result only; it does not grant approval, release, merge, install, workflow, or execution authority.
- H15 performs no executor invocation and no mutation of repository refs or governance state.
- CI remains authoritative for implementation correctness and evidence generation.

## Output

The boundary emits schema `research-os-executor-result/v1` with `read_only=true` and `authority=none`.

The result fingerprint is deterministic over the validated envelope.
