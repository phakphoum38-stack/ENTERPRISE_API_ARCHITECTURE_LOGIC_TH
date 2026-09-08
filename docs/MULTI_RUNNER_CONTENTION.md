# Multi-Runner Contention

## Goal

Validate that concurrent runners cannot reserve the same job twice and that draining runners are excluded from new work.

```text
                 Job
                  |
             ┌────┴────┐
             ↓         ↓
         Runner-A   Runner-B
             \         /
              \       /
               ↓     ↓
             Reservation
                  |
             Assignment Fence
                  |
            exactly one winner
```

## Reference guarantees

- Concurrent reservation attempts for one job yield one assignment.
- The other attempt receives an assignment conflict.
- A DRAINING runner is not selected for new work when a healthy capable runner exists.

## Production boundary

The test uses an in-process lock. Production correctness requires a durable, transactional reservation/fencing mechanism shared by all scheduler/runner instances.
