# V3 Runtime 10^1000 Assurance Protocol

This document defines a bounded assurance protocol whose coverage target is expressed as 10^1000 logical assurance combinations. It does not create 10^1000 runtime objects, workers, queues, executions, tests, or GitHub jobs.

## Purpose

The protocol composes finite independently verified dimensions into a large logical coverage space while keeping execution bounded, deterministic, and auditable.

It preserves these boundaries:
- existing V3 Queue is the durable task boundary;
- existing WorkerPool is the execution primitive;
- existing EventDelivery is the durable event/delivery boundary;
- existing DLQ/Replay is the recovery boundary;
- Workflow Engine remains workflow state authority;
- evidence is observation, not authority;
- replay never creates a second logical task;
- stale ownership is never an authorized completion path.

## Assurance dimensions

The logical space is the Cartesian product of:
- workflow lifecycle: planned, queued, running, completed, failed, interrupted, recovered
- task state: queued, running, retry_wait, completed, failed, dlq
- lease state: absent, active, renewed, expired, reclaimed, stale
- worker state: online, draining, drained, crashed, restarted, shutdown
- event state: absent, appended, registered, duplicated, replayed
- delivery state: available, leased, acked, expired, reclaimed, stale
- DLQ state: available, replaying, replayed, rejected
- restart condition: none, task restart, event restart, full restart
- contention: none, task contention, delivery contention, replay contention
- identity condition: conserved, duplicate, missing, malformed, mixed-target
- evidence state: absent, observed, hashed, manifest-bound, target-bound
- target identity: valid, malformed, mismatched, mixed
- recovery outcome: not-needed, recovered, rejected, quarantined
- authority state: observation, validation, review, pre-authority, owner-authority

The 10^1000 target is a logical coverage cardinality, not an instruction to materialize every combination.

## Composition rule

A scenario signature is the canonical tuple:
workflow.task.lease.worker.event.delivery.dlq.restart.contention.identity.evidence.target.recovery.authority

A valid signature must:
1. canonicalize the signature;
2. validate every dimension against its declared domain;
3. reject unknown values;
4. reject missing required dimensions;
5. reject mixed target identities;
6. reject malformed target identities;
7. preserve task/event/delivery/idempotency identity across replay;
8. reject stale ownership completion;
9. bind evidence to the exact declared target;
10. emit a deterministic evidence fingerprint.

## Coverage amplification

If dimensions contain n1 through nk values, the logical space is the product of all dimension cardinalities. Additional orthogonal predicates can multiply the assurance space without additional runtime executions. Each predicate is independently tested against representative boundary cases and composed algebraically.

This permits a coverage target such as 10^1000 while keeping actual execution finite.

## Fail-closed rules

A signature is FAIL-CLOSED when:
- target SHA is absent or malformed;
- target SHA differs from the evidence target;
- evidence hash is absent or malformed;
- required identity is missing;
- replay changes task identity;
- duplicate idempotency key creates a second logical execution;
- stale owner can acknowledge or complete;
- recovered lease can be completed by its old owner;
- unknown event is silently accepted;
- restart loses durable delivery state;
- an unobserved result is treated as PASS;
- an authority state is inferred from observation alone.

No FAIL-CLOSED case may be promoted by implication.

## Deterministic evidence

Every observed case uses:
- exact target commit identity;
- explicit evidence hashing algorithm;
- canonical JSON encoding;
- sorted object keys;
- stable scenario signature;
- explicit PASS/FAIL result;
- structured observations.

Evidence identity is distinct from Git commit identity:
- Git target identity: 40 hexadecimal characters;
- evidence/artifact identity: SHA-256, 64 hexadecimal characters.

## Replay conservation invariant

For every replay:
- task_id(original) == task_id(replay)
- event_id(original) == event_id(replay)
- idempotency_key(original) == idempotency_key(replay)

A replay may introduce a distinct replay_id, but must not introduce a second logical task.

## Ownership invariant

For lease transition claim(owner=A) -> recover -> claim(owner=B):
- ACK(A) = REJECT
- ACK(B) = ACCEPT only when B owns the active lease.

The same invariant applies to durable event delivery.

## Restart invariant

Restart must preserve durable state required to recover the logical operation.

For repeated recovery crash -> recover -> reclaim -> execute -> ACK, the final durable state must remain consistent with the idempotency contract.

## Bounded execution protocol

Use representative sampling rather than exhaustive materialization.

Minimum execution classes:
- every dimension boundary;
- every pairwise interaction;
- every ownership transition;
- every restart transition;
- every replay transition;
- every identity mutation attempt;
- every evidence/target mismatch;
- every fail-closed condition.

Higher-order combinations are represented by deterministic composition proofs and hashes.

## Evidence manifest contract

A manifest contains:
- protocol identifier;
- protocol version;
- target SHA;
- target identity algorithm;
- evidence algorithm;
- dimension definitions;
- executed scenario IDs;
- scenario result;
- observations;
- evidence hash;
- manifest hash.

The manifest must be reproducible from the same source inputs and target SHA.

## Review boundary

This protocol produces assurance evidence only. It does not:
- grant merge authority;
- grant owner authority;
- modify branch protection;
- modify repository permissions;
- dispatch unrelated workflows;
- create competing execution engines;
- rewrite history;
- silently repair production state.

The authority sequence remains:
Validation -> Independent Review -> Pre-Authority -> Owner Authority -> Merge

## Operational loop

DISCOVER -> INVENTORY -> VERIFY -> EVIDENCE -> DRIFT DETECT -> RECONCILE -> VERIFY AGAIN -> CONTINUE

Every continuation point must identify:
- exact target;
- completed assurance sets;
- remaining assurance sets;
- evidence manifest;
- unresolved failures.

## 10^1000 interpretation

10^1000 is a coverage-design objective. It means the protocol can reason over a combinatorial assurance space of at least 10^1000 logical configurations through compositional dimensions and invariants.

It does not mean:
- 10^1000 GitHub Actions runs;
- 10^1000 processes;
- 10^1000 queue messages;
- 10^1000 database rows;
- 10^1000 files;
- 10^1000 network requests.

This distinction is mandatory to prevent resource amplification and accidental denial of service.

## Completion criteria

The protocol is complete for a target SHA only when:
1. all declared dimensions have explicit domains;
2. all critical boundary predicates have tests;
3. identity conservation is verified;
4. ownership/fencing is verified;
5. restart/recovery is verified;
6. replay/idempotency is verified;
7. evidence is deterministic;
8. evidence is target-bound;
9. manifest is internally consistent;
10. forensic review confirms only intended source changes;
11. independent review packet is complete;
12. pre-authority review is complete.

Owner authority and merge remain separate final actions.
