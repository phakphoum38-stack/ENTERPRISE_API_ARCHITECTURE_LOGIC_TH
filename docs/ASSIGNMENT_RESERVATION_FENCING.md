# Assignment / Reservation / Fencing

## Goal

Close the race between scheduler selection and runner state changes.

```text
Scheduler selects Runner-A
        |
        v
Re-check healthy state
        |
        v
Atomic reservation
        |
        v
Assignment(job -> runner)
```

## Rules

- A job may have at most one active reference assignment.
- Repeating the same reservation for the same job/runner is idempotent.
- A different runner cannot steal an existing assignment.
- A runner that becomes DRAINING or STALE must not receive a new assignment.
- Production must persist the reservation and enforce fencing transactionally with the durable JobStore.

## Important boundary

The reference implementation uses an in-process lock only to validate semantics. It is not a distributed lock and is not production persistence.
