# Research OS — DLQ + Retry Integration

## Purpose

Integrate retry exhaustion with the existing durable event-delivery ledger and the existing V3 DLQ. This is a failure-handling boundary, not a new queue or runner.

## Contract

- DurableEventDelivery owns delivery leases and the durable attempt counter.
- A worker failure is reported only while the worker owns the lease.
- Retryable failure before max_attempts releases the lease and returns the delivery to available.
- Terminal failure persists a DLQRecord before finalizing the delivery as dlq.
- Non-retryable failure goes directly to DLQ.
- A terminal delivery is never ACKed.
- DLQ persistence is idempotent across a crash window between DLQ persistence and delivery finalization.
- Replay remains the existing DLQService/ReplayAdapter path and must enqueue through the existing queue boundary.

## Identity

The DLQ record preserves the original event_id, delivery_id, and idempotency_key. Replay does not mutate the original event evidence.

## Recovery

The existing delivery lease recovery remains responsible for expired worker ownership. DLQ replay recovery remains responsible for records left in REPLAYING.

## Explicit non-goals

- no second queue
- no direct runner invocation from DLQ
- no silent ACK on failure
- no overwrite of another resource/version
