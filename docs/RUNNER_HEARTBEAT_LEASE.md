# Runner Heartbeat + Lease Renewal

## Purpose

Prevent long-running jobs from being reclaimed while their runner is still healthy.

## Lifecycle

```text
CLAIM
  |
  v
LEASE --------------+
  |                 |
  | heartbeat       | expiry
  v                 v
RENEW            RECLAIM
  |                 |
  +----> RUNNING <-+
```

A heartbeat must present the current lease identifier. An expired or stale lease is rejected and cannot be used to complete or mutate the job.

## Reference implementation

`reference/lease.py` provides a small lease manager around the reference JobStore. It intentionally keeps persistence in JobStore and does not store job state inside the runner.

## Production requirements

- heartbeat interval must be shorter than the visibility timeout
- lease renewal must be idempotent
- stale lease owners must be fenced
- renewal failure must trigger controlled runner behavior
- long jobs must not rely on process-local state for recovery
