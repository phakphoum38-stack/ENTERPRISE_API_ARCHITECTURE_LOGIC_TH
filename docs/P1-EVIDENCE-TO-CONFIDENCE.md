# P1 — Evidence → Confidence Boundary

## Purpose

Workset 5 projects validated LearningEvidence into a deterministic confidence
record. It is a data boundary only: confidence does not execute, promote, or
mutate a learned skill.

## 10^1000 coverage model

The assurance space is treated as a logical coverage model of up to 10^1000
scenario combinations. Execution remains bounded. The boundary therefore
aggregates only the evidence records actually supplied and never creates
10^1000 jobs, workers, processes, queues, or rows.

## Contract

- Evidence identity, test identity, and result hash must be 64-character
  lowercase SHA-256 identities.
- Evidence must declare a non-empty sandbox identity and boolean pass state.
- Empty or malformed evidence fails closed.
- Failed evidence contributes zero passed evidence and cannot raise the score.
- Aggregation is order-independent and deterministic.
- Score is passed_count / evidence_count, bounded to [0, 1].
- Zero passed evidence produces HOLD; any passed evidence produces CONFIDENT.
- The confidence record carries an aggregate evidence fingerprint and
  deterministic confidence identity.
- This boundary has no execution, scheduler, worker, queue, promotion, or Core
  Skill mutation authority.

## Authority boundary

Observation → Pattern → Candidate → Sandbox → Test → Evidence → Confidence

The next stage is a separate promotion gate. A CONFIDENT record is not
promotion or merge authorization.

## Determinism

The aggregate is canonicalized by stable evidence identity and hashed with
SHA-256. Reordering the same evidence set produces the same confidence record.
No timestamps or runtime-local values are included in the identity.

## Failure behavior

Malformed identities, missing sandbox identity, empty evidence, and invalid
boolean state fail closed with ValueError. A valid failed evidence record is
preserved as failed evidence and yields zero contribution.

## Non-goals

This workset does not execute candidate procedures, rerun tests, infer new
observations, mutate Core Skills, schedule work, add workers, add queues, or
change existing runtime execution paths.
