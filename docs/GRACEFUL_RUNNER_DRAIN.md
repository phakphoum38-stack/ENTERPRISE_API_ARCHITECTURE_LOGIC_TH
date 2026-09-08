# Graceful Runner Drain

## Goal

Allow a runner to stop accepting new work while allowing already-assigned work to finish safely.

```text
ONLINE
  |
  | drain()
  v
DRAINING
  |
  | active jobs finish
  v
DRAINED
  |
  v
SHUTDOWN
```

## Rules

- `DRAINING` runners are excluded from new scheduling assignments.
- Jobs already assigned to the runner remain active.
- The runner may shut down only after its active-job count reaches zero.
- A new job attempt against a draining runner is rejected.
- Job/lease state remains in the shared execution state; the controller is only a reference lifecycle layer.

## Production requirements

The production implementation must coordinate drain state with durable assignment state, lease fencing, cancellation, shutdown deadlines, and process termination signals.
