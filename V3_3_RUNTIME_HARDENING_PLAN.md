# V3.3 Runtime Hardening Plan

Status: Proposed implementation plan
Baseline: `main` @ `c0ffe5dbc36f2f8c9ec869e08bc34aec9f8c3126`

## Goal

Harden the existing V3 runtime for distributed production execution without introducing a parallel queue, runner, or tracker implementation.

## Scope

### 1. Lease and ownership

Extend the existing queue claim model with explicit ownership:

- `lease_id`
- `lease_until`
- owner identity
- renew operation
- ownership-checked ack/nack
- expired lease recovery

Acceptance:

- only the current lease owner can ack/nack
- expired work can be reclaimed safely
- renewal extends an active lease only
- duplicate completion is harmless

### 2. Worker pool

Extend the existing stateless runner with a bounded worker pool:

- configurable concurrency
- per-worker lifecycle
- graceful shutdown
- cancellation handling
- queue polling/backoff
- integration with lease renewal

Acceptance:

- concurrency never exceeds configured limit
- shutdown does not lose acknowledged work
- worker crash leaves work recoverable
- all workers share the existing queue contract

### 3. Dead-letter queue

Extend existing retry/failure semantics:

- terminal failure after max attempts
- durable DLQ record
- failure reason and attempt history
- inspect operation
- explicit replay operation

Acceptance:

- exhausted retries are never silently discarded
- replay creates a new controlled delivery attempt
- DLQ state survives process restart

### 4. Event delivery and idempotency

Implement delivery around the existing workflow-runtime event contract:

- durable event identity
- delivery attempt tracking
- consumer idempotency key
- duplicate suppression
- replay support

Acceptance:

- duplicate delivery does not duplicate side effects
- event state survives restart
- failed delivery can be retried
- replay is observable

## Non-goals

- no replacement queue
- no replacement runner
- no second work tracker
- no breaking V3.2 contract changes
- no deletion of V1/V2 compatibility surfaces in this phase

## Required tests

- lease claim / renew / expiry
- ownership violation
- ack / nack idempotency
- worker concurrency limit
- graceful shutdown
- worker crash recovery
- retry exhaustion to DLQ
- DLQ replay
- duplicate event delivery
- event replay
- restart durability
- 10x10 runtime evidence

## Release gate

`feature/v3-runtime-hardening` must not merge until implementation, unit tests, integration tests, failure-injection tests, and E2E evidence all pass against the same commit SHA.
