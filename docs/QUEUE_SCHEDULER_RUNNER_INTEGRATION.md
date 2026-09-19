# Queue -> Scheduler -> Assignment -> Runner

## Reference flow

```text
Queue
  |
  v
Orchestrator
  |
  v
Scheduler
  |
  v
Runner Registry
  |
  v
Atomic Assignment
  |
  v
Runner
  |
  v
JobStore / Execution Loop
```

The orchestration boundary keeps scheduling decisions separate from execution. The Queue carries work, Scheduler chooses a healthy/capable target, Assignment fences the decision, and the Runner executes through the existing lease-aware execution path.

## Production boundary

This reference flow intentionally does not claim distributed atomicity. Production must make queue delivery, assignment reservation, lease ownership, and completion durable and transactionally safe enough to prevent double execution under retries and races.
