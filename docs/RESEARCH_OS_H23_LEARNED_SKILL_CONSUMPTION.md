# Research OS H23 — Learned Skill Consumption Boundary

## Contract

H23 turns an approved learned-skill registry entry into a bounded, immutable consumption envelope.

```text
H22 LEARNED SKILL REGISTRY
        │
        ▼
H23 CONSUMPTION BOUNDARY
        │
        ▼
H24 ACTIVATION AUTHORITY
```

H23 does not execute the skill. It verifies identity, version, registry integrity, approval state, and bounded payload safety before handing a read-only envelope to H24.

## Required invariants

- Skill must exist in the learned-skill registry.
- Skill status must be `approved`.
- Requested version must match the registry entry exactly.
- Registry snapshot must be immutable (`tuple`).
- Registry SHA-256 fingerprint must match the supplied fingerprint.
- Candidate content is bounded and scanned for unsafe execution, credential, release, merge, install, dispatch, and bypass content.
- Output schema is `research-os-learning-skill-consumption/v1`.
- Output is `read_only: true` with `authority: none`.
- Execution authority is explicitly deferred to H24.

## Authority boundary

H23 cannot approve, promote, execute, release, install, merge, dispatch, mutate refs, or rewrite evidence.

## Evidence

The H23 unit tests are the executable contract. CI is authoritative. This document is design context only.
