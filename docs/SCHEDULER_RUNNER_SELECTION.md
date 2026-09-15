# Scheduler + Runner Selection

## Goal

Select an execution target from the shared Runner Registry without coupling the Workflow Engine to a concrete runner process.

```text
Job
 |
 v
Scheduler
 |
 +--> ONLINE?
 |
 +--> DRAINING?
 |
 +--> STALE?
 |
 +--> capability match?
 |
 v
Runner
```

## Reference policy

The reference scheduler uses deterministic first-fit ordering by `runner_id`. Production scheduling can replace this policy with capacity, locality, queue depth, tenant, priority, cost, or affinity scoring without changing the registry boundary.

## Safety rules

- Never select STALE runners.
- Never select DRAINING runners for new work.
- Capability requirements must be satisfied.
- No available runner is an explicit scheduling failure, not a silent fallback.

## Next

- integrate scheduling with Queue delivery
- add priority/capacity scoring
- add reservation/assignment fencing
- add graceful drain
- add multi-runner integration and load tests
