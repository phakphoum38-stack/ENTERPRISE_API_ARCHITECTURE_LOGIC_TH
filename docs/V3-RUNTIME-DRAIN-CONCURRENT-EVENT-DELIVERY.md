# V3 Runtime Hardening — Drain, Concurrent Claims, Event Delivery

This slice closes three forensic gaps against main b52f6852fd1085c72fb947fead3e4da5a26759a7 without adding a second queue, runner, worker pool, or event bus.

## C — concurrent multi-runner claim proof

DurableTaskQueue.claim() already uses a SQLite BEGIN IMMEDIATE transaction and a queued-row predicate. The new concurrency regression starts two workers simultaneously against one task and requires exactly one claimant.

Existing crash-recovery tests remain authoritative for stale-lease fencing: a reclaimed task receives a new lease and the crashed worker cannot acknowledge it.

## B — graceful drain boundary

The existing BoundedWorkerPool remains the only worker-pool execution primitive. It now exposes:

ONLINE → DRAINING → DRAINED → SHUTDOWN

Entering DRAINING closes admission immediately. Accepted work is allowed to finish. DRAINED is reached only after active work reaches zero, after which shutdown terminates the existing executor.

No scheduler, queue, worker pool, or execution engine is introduced.

## E — durable event delivery

The existing current/workflow-runtime/events.yml contract remains the source event schema: event identity, workflow/task correlation, sequence, producer, payload, at-least-once delivery, and idempotent consumers.

DurableEventDelivery adds only the missing persistence boundary:

- append-only event records keyed by event_id
- durable delivery records keyed by delivery_id
- stable idempotency_key uniqueness
- per-delivery lease ownership
- atomic claim under SQLite transaction
- idempotent acknowledgement
- stale-lease recovery after restart

It does not execute handlers, publish a second bus, or replace the existing queue/runner path.

## Acceptance boundary

The implementation is intentionally not certified by CI in this change. Workflows are not dispatched by this forensic pass.

Required evidence before promotion:
1. concurrent claim: exactly one winner
2. stale queue lease cannot acknowledge after reclaim
3. drain rejects new admission and reaches DRAINED only after active work reaches zero
4. duplicate event registration is suppressed by idempotency key
5. only one delivery lease holder can acknowledge
6. expired delivery can be recovered and reclaimed
7. durable acknowledgement survives process restart
8. existing V3/DLQ/replay tests remain green against the same commit

Merge/authority boundaries remain unchanged.