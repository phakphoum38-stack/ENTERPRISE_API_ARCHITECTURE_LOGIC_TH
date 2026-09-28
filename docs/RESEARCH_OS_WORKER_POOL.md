# Research OS — Stateless Worker Pool Contract

The worker pool is an execution layer over the existing DurableEventDelivery ledger. It does not introduce a second queue, tracker, or event bus.

## Guarantees

- bounded process-local concurrency
- workers are stateless; durable ownership lives in the delivery lease
- successful handlers ACK using the claimed lease
- failed handlers do not ACK, leaving work recoverable by lease expiry
- duplicate completion is harmless because delivery ACK is idempotent
- multiple runner processes can share the same durable delivery contract

## Production boundary

Queue/event persistence, lease ownership, recovery, and idempotency remain the source of truth. A runner may disappear at any time; after lease expiry another runner can reclaim the delivery.

Retry/DLQ remains in the existing dedicated V3 DLQ surfaces; this module does not create a second delivery path.
