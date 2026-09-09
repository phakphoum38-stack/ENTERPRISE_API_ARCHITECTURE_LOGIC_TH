# Research OS H3 — Mission Control / Guarded Automation Boundary

**Status:** IMPLEMENTATION DRAFT — verification required
**Base:** `c04d60b36d51eb8529a4c65a61c7d5a411e5fe85`
**Mode:** `AUTO_GUARDED`

## Purpose

H3 binds the existing Mission Control read-only path to the H2 Evidence/Provenance contract and an exact-SHA verification boundary. H3 may observe, validate, diagnose, and propose work, but it does not become an execution, approval, authorization, release, or merge authority.

## Canonical path

```text
Exact Main SHA
  -> H2 Evidence / Provenance
  -> 4H Unified Snapshot
  -> 4I UI Projection
  -> 5A Desktop Surface
  -> Negative / Adversarial Tests
  -> Authority Audit
  -> Certification
```

The existing 4H snapshot is explicitly an aggregation/read-only boundary and must not execute tools, providers, workflows, authorization, approval, or runtime mutation. citeturn136file0

## Guarded automation rules

1. Every operation captures the exact source SHA before verification.
2. A changed SHA invalidates downstream evidence and requires re-anchoring.
3. H2 evidence is descriptive proof, never authority.
4. UNKNOWN, stale, missing, conflicting, or owner-mismatched evidence fails closed at an authority boundary.
5. H3 may propose/diagnose/verify; it cannot approve, release, merge, dispatch workflows, or escalate capability.
6. UI projection remains presentation-only and cannot acquire execution authority. citeturn140file0
7. PASS/FAIL/PENDING/UNKNOWN are preserved and never reinterpreted as approval.
8. Certification requires exact-SHA verification plus authoritative CI evidence.
9. No generated evidence is fabricated by H3.
10. No autonomous component may modify the rules that evaluate that component.

## Auto readiness

`AUTO_GUARDED` is the active target mode for H3. Auto-merge is explicitly disabled by this contract. Promotion to autonomous merge requires a separately governed contract, verified negative tests, provenance evidence, and post-merge verification.

## Exit criteria

H3 is ready for promotion only when the exact base SHA is preserved, the Mission Control path remains read-only, adversarial tests pass, authority boundaries remain intact, evidence/provenance is bound, and authoritative CI verifies the exact head SHA.
