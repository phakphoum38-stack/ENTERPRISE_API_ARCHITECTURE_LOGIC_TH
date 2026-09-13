# H9 — Repair Verification

## Purpose

H9 closes the verification loop after an Autobot repair. A repair is never considered successful merely because a file changed or a commit was created.

## Contract

```text
REPAIR
  -> NEW COMMIT SHA
  -> H0 IDENTITY CAPTURE/BINDING
  -> FRESH CI EVIDENCE
  -> SHA + CORRELATION VALIDATION
  -> PROVENANCE VALIDATION
  -> PASS / FAIL / BLOCKED
```

### Required invariants

- The repair commit must be a valid 40-character lowercase Git SHA.
- The repair commit must differ from the source SHA.
- CI evidence must reference the repair commit exactly.
- CI evidence must use the same bounded correlation ID.
- Evidence must be fresh and provenance must terminate at the displayed CI evidence.
- PASS is accepted only from explicit CI PASS evidence.
- Missing, stale, conflicting, malformed, secret-like, or authority-bearing evidence fails closed.
- A failed verification remains a failure and never becomes PASS by heuristic inference.
- Verification is read-only policy/state logic.
- H9 does not dispatch workflows, mutate refs, approve, merge, release, install, execute shell/process/MCP/Computer Use actions, or fabricate evidence.

CI and existing provenance gates remain authoritative.
