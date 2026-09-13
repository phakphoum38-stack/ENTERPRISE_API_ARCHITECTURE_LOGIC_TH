# Research OS H24 — Learned Skill Activation Boundary

## Contract

H24 converts a validated H23 consumption envelope into a bounded activation envelope for H25.

```text
H23 CONSUMPTION
      │
      ▼
H24 ACTIVATION
      │
      ▼
H25 EXECUTOR RESULT
```

H24 is an activation boundary, not an executor. It does not run the learned skill.

## Required invariants

- H23 schema must be `research-os-learning-skill-consumption/v1`.
- Consumption state must be `READY_FOR_GOVERNED_USE`.
- H23 must remain `read_only: true` and `authority: none`.
- H23 must identify H24 as the activation authority.
- Owner, skill name, skill version, and consumption fingerprint must match exactly.
- Activation ID is bounded and cannot contain authority, execution, credential, release, install, merge, dispatch, or bypass terms.
- Skill payload remains bounded and recursively scanned.
- Output is `research-os-learning-skill-activation/v1` with `READY_FOR_H25` state.
- H25 is the downstream execution/result boundary; H24 itself performs no execution.

## Authority boundary

H24 cannot promote, approve, execute, release, install, merge, dispatch, mutate refs, or rewrite evidence.

## Evidence

The H24 Python tests are the executable contract. CI is authoritative. This document is design context only.
