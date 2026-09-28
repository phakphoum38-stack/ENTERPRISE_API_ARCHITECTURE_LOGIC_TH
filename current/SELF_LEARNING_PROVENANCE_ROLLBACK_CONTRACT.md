# Self-Learning Provenance & Rollback Contract

Phase 1 continuation of the bounded Self-Learning 2.0 architecture.

## Contract

1. Every reusable learned-skill version may carry immutable provenance.
2. Provenance binds the skill version to its source, generator, evidence references, evaluation score, confidence, and parent version.
3. Feedback remains evidence. It does not directly promote or mutate a skill.
4. A rollback is an immutable plan, not an execution operation.
5. Rollback targets must point to an older version.
6. Approval/execution authorities remain outside this data model.
7. Core Skills remain outside the Learned Skill Registry and are never mutated by this boundary.
8. A missing rollback target is an explicit planning error, not an implicit fallback.

## Lifecycle

`experience -> candidate -> validate -> evaluate -> promote -> provenance -> feedback -> evaluate -> version proposal -> sandbox -> promote`

Regression path:

`negative feedback -> evidence -> rollback plan -> approval gate -> explicit rollback`

This contract intentionally does not execute rollback, mutate registries, invoke tools, access credentials, or trigger workflows.
