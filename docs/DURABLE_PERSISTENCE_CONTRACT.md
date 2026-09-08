# Durable Persistence Contract

## Purpose

Keep execution state outside stateless runners and make the production storage boundary explicit before implementing a database adapter.

## Core records

- `JobRecord` — workflow job state, payload, attempt number, timestamps.
- `AssignmentRecord` — job-to-runner ownership, lease, status, and fencing token.
- `AttemptRecord` — execution attempt and result metadata.
- `RunnerRecord` — runner identity, health state, capabilities, and heartbeat timestamp.

## Required invariants

1. A job has at most one active assignment.
2. Reservation is atomic and produces a monotonically increasing fencing token for the job/assignment lineage.
3. Renew and complete operations must validate assignment identity and fencing token.
4. A stale token must never mutate current execution state.
5. Expired assignments can be reclaimed and a new attempt can be created.
6. Runner processes do not own durable job state.

## Adapter boundary

`DurablePersistence` is a Python protocol. PostgreSQL, Redis-backed coordination, or another durable implementation can satisfy it without changing Scheduler or Runner APIs.

## Production transaction requirements

The durable adapter must define transaction boundaries for reservation, fencing-token issuance, lease renewal, completion, and reclaim. Database-specific locking or conditional updates belong inside the adapter, not in the domain layer.
