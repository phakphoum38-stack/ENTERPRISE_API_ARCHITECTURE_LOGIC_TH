# Autonomous Engineering OS — Implementation Plan

## Phase 0 — Freeze and Observe

- Keep H26 and H27 reserved.
- Do not create new feature work inside the H0→H24 drain unless it is a root-cause, regression, security, provenance, or re-anchoring fix.
- Snapshot main SHA and queue state before autonomous processing.
- Treat PR metadata as hints; ancestry and diff are authoritative.

## Phase 1 — Guarded Queue

Implement machine-readable queue states:

`DISCOVERED → CLASSIFIED → ELIGIBLE → PROCESSING → VERIFYING → CERTIFIED → MERGED → POST_VERIFIED`

Failure transitions:

`ANY → HOLD → FORENSICS → RECOVERY`

## Phase 2 — Proof Fabric

Add common structures for:

- exact SHA identity
- evidence fingerprints
- provenance bindings
- contract version
- policy version
- verifier identity
- validity scope
- decision replay inputs

## Phase 3 — Change Certificate

Generate one immutable certificate per certified merge. The certificate must reference the exact source and target identities and the recovery point.

## Phase 4 — Forensic Memory

Persist structured records for:

- symptom
- detector
- introducer
- root cause
- affected components
- fix
- regression
- evidence
- prevention rule
- confidence

## Phase 5 — Autonomous Repair Boundary

Permit bounded repair only within declared capability and protected-path rules. Foundation, trust, authority, provenance, and constitutional files require elevated governance.

## Phase 6 — Post-Merge Assurance

After every merge:

1. fetch main
2. verify expected merge SHA
3. run health checks
4. verify canonical contracts
5. verify evidence/provenance roots
6. record new recovery point
7. invalidate stale downstream evidence
8. rebuild queue

## Phase 7 — Counterfactual / Shadow Evaluation

For high-risk changes, compare candidate outcomes before canonical mutation. Shadow evaluation must never be treated as proof for a different SHA.

## Phase 8 — Immune System

Promote verified recurring failures into:

`detector → regression → preventive rule`

No failure may directly rewrite constitutional policy.

## Phase 9 — H0→H24 Drain

The drain proceeds one dependency-safe unit at a time. The next unit is selected only after the current merge is post-verified and main is re-read.

## Phase 10 — Horizon Promotion

Only after H0→H24 reaches a stable certified state may the governance owner decide whether H25 becomes eligible. H26/H27 remain reserved until explicitly released.

## Non-Negotiable Safety Rules

- Never merge from a stale branch merely because CI is green.
- Never reuse evidence across an invalidated SHA boundary.
- Never allow an agent to approve its own trust claim.
- Never weaken a test or contract to make automation green.
- Never treat UNKNOWN as VERIFIED.
- Never continue the queue after post-merge health failure.
- Never silently discard failed evidence.
- Never rewrite canonical history as an autonomous shortcut.

## Success Condition

AEOS is successful when autonomous execution becomes faster **without reducing the system's ability to explain, prove, audit, reproduce, and recover every material state transition**.
