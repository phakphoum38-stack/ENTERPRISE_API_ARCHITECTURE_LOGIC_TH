# JobStore Reference Claim Semantics

This document defines deterministic scenarios for the first reference implementation.

## Concurrent claim

Given one `QUEUED` job and runners A, B, and C:

- exactly one runner may transition the job to `CLAIMED`
- the winning runner receives the active `lease_id`
- losing runners receive a conflict/no-claim result

## Lease expiry

Given runner A owns a lease that expires:

1. runner A stops heartbeating
2. the lease becomes expired
3. runner B may reclaim the job
4. runner A's old lease must be fenced
5. runner A must not be able to complete the reclaimed job

## Idempotent create

Two creates with the same `idempotency_key` must resolve to the same logical job and must not create two runnable jobs.

## Duplicate delivery

If the queue delivers the same message more than once, processing must remain safe because job claim and completion are lease-fenced and idempotent.

## Terminal protection

`SUCCEEDED`, `CANCELLED`, and `DEAD_LETTER` jobs must never be returned by normal runnable-job polling.

These scenarios are acceptance-test requirements, not a claim that a production adapter has already been implemented.
