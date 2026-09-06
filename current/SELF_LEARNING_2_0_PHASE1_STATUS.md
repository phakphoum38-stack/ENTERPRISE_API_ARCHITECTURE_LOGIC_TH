# Self-Learning 2.0 — Phase 1 Status

## Branch

`phase1/self-learning-provenance`

Base: `main` at `ee3b822073eaa092ccba3e19405dd2c3993903bc`.

## Implemented on this branch

1. Version proposals with explicit parent lineage.
2. Feedback as evidence-only input.
3. Immutable provenance records for learned-skill versions.
4. Append-only provenance ledger with monotonic version enforcement.
5. Explicit rollback plans; rollback is never performed by planning code.
6. Immutable evaluation records bound to an exact skill version.
7. Append-only evaluation history.
8. Feedback aggregation for observation/reporting only.
9. Version-mismatch protection between candidates and feedback.
10. Immutable promotion evidence bundles and append-only promotion history.
11. Deterministic v1-to-v2 revision proposals bound to the parent version.
12. Revision evaluation binding: v2 evaluation is bound to the v2 candidate while feedback remains explicitly bound to v1.
13. Regression tests for provenance, rollback, evaluation history, feedback aggregation, promotion history, and revision lineage.

## Safety boundary

Self-learning remains data-driven and bounded. No code generation is executed, no tool is executed, no credential is persisted, and no Core Skill is mutated by these primitives.

Promotion remains a separate authorization decision. Evaluation, feedback, provenance, and promotion history provide evidence and auditability; they do not grant authority by themselves.

Rollback remains a plan until an explicit approval/execution boundary exists.

## Phase 1 completion criteria

Phase 1 is structurally complete when a learned skill can be represented as an immutable lineage:

`v1 -> feedback(v1) -> revision proposal(v2,parent=v1) -> candidate(v2) -> evaluation(v2) -> provenance(v2) -> promotion evidence(v2) -> promotion record(v2)`

The revision cycle intentionally does not auto-promote v2. Promotion must still be performed through the dedicated promotion authority and remain inspectable through the promotion ledger.

## Workflow policy

No GitHub Actions workflow was intentionally executed while developing this branch. Workflow execution remains an explicit release/verification action.
