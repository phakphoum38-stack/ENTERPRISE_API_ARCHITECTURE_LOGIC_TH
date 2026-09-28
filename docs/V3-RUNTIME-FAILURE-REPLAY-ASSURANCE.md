# V3 Runtime Failure and Replay Assurance

## Purpose

This workset verifies failure semantics around the existing V3 queue, lease/ownership boundary, worker pool, durable event delivery, and DLQ/replay path.

It does not introduce a second queue, runner, worker pool, event bus, scheduler, or execution engine.

## Failure matrix

| Failure | Required invariant | Evidence |
| --- | --- | --- |
| concurrent task claim | exactly one lease owner | queue concurrency test |
| stale task owner | old lease cannot mutate state | lease fencing test |
| expired task lease | task becomes claimable by a new owner | recovery + fencing test |
| active task owner | renewal preserves ownership | lease renewal test |
| duplicate event registration | same idempotency key maps to one delivery | event delivery test |
| concurrent delivery claim | one active delivery owner | event delivery test |
| stale delivery owner | old lease cannot acknowledge after recovery | event delivery test |
| event ledger restart | acknowledged state survives reopen | event delivery test |
| unknown event | delivery registration fails closed | event delivery test |
| replay/recovery | delivery returns through existing queue boundary | existing V3.4 recovery/E2E tests |

## Verification boundary

All checks must execute against the exact PR head SHA. A passing test from another commit is not evidence for this workset.

The workset is test/evidence hardening only unless a concrete implementation defect is demonstrated. Existing runtime architecture remains authoritative.

## Completion rule

Promotion requires:

1. unit tests pass on the exact target SHA;
2. failure/recovery evidence is deterministic and inspectable;
3. no duplicate execution path is introduced;
4. independent review and pre-authority checks complete;
5. Owner Authority remains the final merge decision boundary.
