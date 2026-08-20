# V3.4 — DLQ + Replay Design

## Scope

V3.4 adds durable failure handling and controlled replay on top of the existing V3 queue, Worker Pool, and Lease/Ownership runtime.

It does **not** introduce a second queue, runner, ownership model, or execution engine.

## State machine

```text
QUEUED
  -> RUNNING
      -> SUCCEEDED
      -> FAILED
           -> RETRY_WAIT -> QUEUED
           -> DLQ
                -> REPLAYING
                     -> QUEUED
                     -> REJECTED
```

## DLQ record contract

Required fields:

- `task_id` — stable original task identifier
- `event_id` — stable source event identifier
- `delivery_id` — delivery attempt identifier
- `idempotency_key` — stable duplicate-prevention key
- `lease_id` — ownership lease associated with the failed execution
- `attempt` — attempt number that failed
- `max_attempts` — retry limit at failure time
- `error_type` — normalized failure class
- `error_message` — bounded diagnostic message
- `first_failed_at`
- `last_failed_at`
- `failed_at`
- `payload_reference` — reference to durable payload/event storage
- `replay_count`
- `status`

Large payloads should remain in the existing durable event/payload store; the DLQ record should reference them rather than duplicate them.

## Replay contract

A replay creates a new `replay_id`, but preserves the original:

- `task_id`
- `event_id`
- `idempotency_key`

Replay must pass through the existing queue and Worker Pool. It must not directly invoke a runner.

Replay metadata:

- `replay_id`
- `replay_count`
- `replayed_at`
- `replayed_by`
- optional `reason`

## Idempotency rules

1. A duplicate replay request for the same active `idempotency_key` must not create a second execution.
2. A completed task must remain completed when an old delivery is replayed.
3. Replay must be auditable.
4. Concurrent replay requests must resolve atomically.
5. Lease acquisition remains the ownership boundary; replay does not bypass it.

## Retry rules

- Retryable failures return to the existing queue through `RETRY_WAIT`.
- Retry exhaustion moves the task to DLQ exactly once.
- Non-retryable failures may move directly to DLQ.
- Every transition must be idempotent.

## Recovery rules

On runner/process restart:

- expired ownership is recovered by the existing Lease/Ownership layer;
- DLQ records remain durable;
- replay requests remain durable;
- no task is silently lost because a worker process exited.

## Security / authorization

Replay is an operational action and must be authorized. The audit record must identify the actor or service principal that initiated replay.

## Acceptance criteria

- retry exhaustion -> durable DLQ
- non-retryable failure -> DLQ
- DLQ survives process restart
- replay returns through the existing queue
- duplicate replay is prevented by idempotency
- concurrent replay is safe
- expired leases remain governed by the existing ownership layer
- replay is auditable
- E2E covers worker crash, restart, replay, and duplicate delivery
