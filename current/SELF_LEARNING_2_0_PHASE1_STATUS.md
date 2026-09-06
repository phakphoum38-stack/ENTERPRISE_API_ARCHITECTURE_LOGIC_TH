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
12. Revision evaluation binding: the evaluation record is bound to the v2 candidate while parent feedback is validated as v1 evidence for the revision.
13. Revision feedback evidence references preserve all supplied evidence refs rather than only the first ref.
14. Bounded lifecycle assembly across candidate, evaluation, provenance, promotion evidence, and promotion decision records.
15. Lifecycle integrity validation across every present stage and exact skill/version/evidence binding.
16. Forward-only stage locks: downstream lifecycle stages prevent rewriting upstream evidence.
17. Readiness predicates for evaluation, provenance, promotion evidence, and complete lifecycle state.
18. Regression tests for provenance, rollback, evaluation history, feedback aggregation, promotion history, revision lineage, lifecycle assembly, integrity, readiness, and stage locks.

## Safety boundary

Self-learning remains data-driven and bounded. No code generation is executed, no tool is executed, no credential is persisted, and no Core Skill is mutated by these primitives.

Normal evaluation records remain exact-version bound. Revision evaluation is the explicit exception that validates parent-version feedback as input evidence while keeping the resulting evaluation record bound to the revision candidate.

The lifecycle assembler only composes immutable evidence. It does not mutate the learned-skill registry, execute tools, or authorize promotion.

Lifecycle integrity is validation-only. A valid lifecycle snapshot means the evidence chain is internally consistent; it does not mean promotion is authorized.

Stage locks are forward-only within an immutable snapshot: evaluation cannot be replaced after provenance exists, provenance cannot be replaced after promotion evidence exists, promotion evidence cannot be replaced after a decision exists, and a decision cannot be replaced once recorded.

Readiness is also non-authorizing: `is_promotion_ready()` means required evidence is assembled, not that an approval has been granted or that promotion should execute.

Promotion remains a separate authorization decision. Evaluation, feedback, provenance, and promotion history provide evidence and auditability; they do not grant authority by themselves.

Rollback remains a plan until an explicit approval/execution boundary exists.

## Phase 1 completion criteria

Phase 1 is structurally complete when a learned skill can be represented as an immutable lineage:

`v1 -> feedback(v1) -> revision proposal(v2,parent=v1) -> candidate(v2) -> evaluation(v2) -> provenance(v2) -> promotion evidence(v2) -> promotion record(v2)`

The lifecycle assembler now provides bounded assembly, integrity validation, readiness inspection, and forward-only stage locking for these evidence stages while intentionally keeping promotion execution outside the lifecycle module.

## Verification state

The revision-cycle implementation has been statically corrected so parent feedback can be used as v2 evaluation evidence without weakening normal exact-version evaluation rules. Lifecycle regression coverage now includes evidence preservation, wrong-parent-version rejection, score bounds, no-auto-promotion behavior, stage-lock enforcement, readiness transitions, and malformed-snapshot integrity detection.

This branch has not had GitHub Actions intentionally executed during development. CI/release verification remains a separate explicit action.

## Workflow policy

No GitHub Actions workflow was intentionally executed while developing this branch. Workflow execution remains an explicit release/verification action.
