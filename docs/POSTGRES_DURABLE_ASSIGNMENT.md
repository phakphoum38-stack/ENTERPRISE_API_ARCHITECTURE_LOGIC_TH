# PostgreSQL Durable Assignment

This adapter is the first production-oriented persistence implementation of the durable assignment contract.

## Invariants

- `job_id` is unique for an active assignment.
- reservation is performed inside the caller-owned database transaction.
- an expired assignment may be reclaimed.
- reclaim increments the fencing token.
- completion must present the current fencing token.
- a stale token cannot complete an active assignment.

## Transaction boundary

The application owns `BEGIN/COMMIT/ROLLBACK`. `PostgresAssignmentStore` executes the reservation/completion statements inside that transaction and does not silently commit.

## Extension points

The next production steps are runner registration persistence, lease renewal, retry/attempt persistence, queue delivery integration, and real PostgreSQL integration tests against a disposable database.
