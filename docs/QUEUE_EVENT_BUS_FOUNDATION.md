# Queue + Event Bus Foundation

## Goal

Establish the production execution boundary between API/workflow submission and stateless runners.

## Flow

```text
API
  -> Event
  -> Durable Queue
  -> Claim / Lease
  -> Stateless Runner
  -> Ack / Nack
  -> Result + Evidence
```

## Contract

The normative contract is `contracts/queue_event_bus.yml`.

### Required guarantees

1. Enqueue is idempotent.
2. A job has at most one active lease.
3. Lease expiry makes an abandoned job claimable.
4. Heartbeat extends a live lease.
5. Nack schedules retry or moves the job to dead letter.
6. Ack is terminal and only follows successful execution.
7. Duplicate events are rejected or safely deduplicated.

## Implementation boundary

This foundation deliberately defines contracts before selecting a concrete broker or database implementation. Adapters may later target Redis Streams, PostgreSQL-backed queues, Kafka, SQS, or another durable transport without changing the workflow execution model.

## Next implementation steps

- implement JobStore
- implement EventStore / EventPublisher
- implement QueueAdapter
- implement atomic claim + lease
- implement heartbeat
- implement ack/nack
- add integration tests
- add runner adapter
- add load and failure tests
