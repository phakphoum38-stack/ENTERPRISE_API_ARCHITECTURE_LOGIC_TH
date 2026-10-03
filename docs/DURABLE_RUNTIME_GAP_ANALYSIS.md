# Durable Queue, Lease and Heartbeat Gap Analysis

Baseline: `main` @ `a06f0b7`

## Current implementation

| Contract requirement | Implementation | Evidence | Status |
|---|---|---|---|
| Durable queue storage | `v3/research_os_v3/queue.py` SQLite `research_queue` table | queue and research execution tests | verified |
| Lease identity and expiry | `lease_id`, `lease_until`, `worker_id` | `test_worker_crash_recovery.py` | verified |
| Ownership-checked ack/fail/retry | active lease validation before mutation | crash recovery and runner tests | verified |
| Lease renewal | `renew_lease()` rejects expired or stale leases | queue/runner tests | verified |
| Expired lease recovery | `recover_expired_leases()` clears ownership and requeues work | worker recovery evidence | verified |
| Retry attempt persistence | queue increments `attempts` on retry | runner and research execution tests | verified |
| Bounded worker pool | `v3/worker_pool.py` | worker pool, shutdown and timeout tests | verified |
| Heartbeat/stale work recovery | `PersistentWorkTracker.heartbeat()` and stale recovery | `test_work_tracker.py`, status recovery E2E | verified, separate tracker |
| DLQ durability/replay | SQLite DLQ store, replay adapter and recovery manager | DLQ/replay/recovery tests | verified |
| Event delivery idempotency | durable workflow event store has consumer claim lease, complete/fail state, attempt count, failed-delivery retry and one-event delivery API | `v3/tests/test_durable_events.py`; existing replay integration tests | partial |
| Durable workflow event log | `v3/research_os_v3/durable_events.py` provides SQLite append-only storage, sequence assignment and delivery claims; runner/queue wiring remains open | `v3/tests/test_durable_events.py` | partial |
| Queue-to-engine state authority | transactional queue outbox publishes idempotently to the durable event store and `WorkflowStateProjector` applies the event stream; distributed engine ownership protocol remains open | `v3/tests/test_queue_outbox.py`, `test_workflow_projection.py` | partial |

## Findings

- Lease ownership and recovery are implemented in the canonical queue and protected by tests.
- Worker pool and DLQ behavior are implemented as adjacent runtime capabilities and do not introduce a replacement queue.
- Heartbeat behavior currently belongs to the persistent work tracker. It must be reconciled with queue lease renewal so a heartbeat cannot imply queue ownership remains valid.
- Runner telemetry is intentionally fail-safe. Queue transitions now have a same-database transactional outbox, an idempotent publisher, bounded `drain_outbox()` worker behavior, a one-shot CLI entry point, local failure/retry evidence and a workflow state projection; runner callback persistence remains a separate path.
- Duplicate replay protection, generic event delivery, expired consumer-lease reclaim and local delivery metrics are durable; production scrape/alert wiring and distributed tracing remain open.

## Required next implementation/tests

1. Define distributed engine ownership and projection deployment protocol.
2. Deploy `v3/scripts/drain_outbox.py` on a scheduler and export delivery metrics.
3. Define how tracker heartbeat renews or observes queue lease without creating two ownership authorities.
4. Add end-to-end restart tests covering queue state, event state, delivery retry and duplicate suppression together.
5. Add lease-race tests for renew versus expiry recovery and ack versus reclaim.
6. Produce `10x10` evidence using the same target SHA as the release gate.

## Release decision

The queue/lease/worker/DLQ foundation is test-verified. The V3.2 workflow contract is not yet production-promoted because durable event delivery and the single state-authority projection remain open.
