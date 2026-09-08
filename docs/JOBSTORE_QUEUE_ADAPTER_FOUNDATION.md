# JobStore + Queue Adapter Foundation

This layer turns the Queue/Event Bus contract into an explicit storage/transport boundary.

## Design

```text
Workflow Engine
      |
      v
 QueueAdapter -----> durable transport
      |
      v
   JobStore --------> durable state
      |
      v
 atomic claim + lease
      |
      v
 Stateless Runner
```

## Required semantics

- Job creation is idempotent.
- Claim is atomic and uses compare-and-set semantics.
- A job has one active lease owner.
- Heartbeat requires the current lease.
- An expired lease may be reclaimed.
- A stale runner cannot complete a job after its lease has been reclaimed.
- Queue delivery is at-least-once and duplicate delivery must be safe.
- Terminal jobs are never returned as runnable work.

## Implementation neutrality

The contract does not mandate a particular database or broker. Concrete adapters must implement these semantics and provide integration evidence.

## Next

1. Implement an in-memory reference adapter for deterministic tests.
2. Implement a durable adapter.
3. Add concurrent claim tests.
4. Add stale-lease fencing tests.
5. Add retry/dead-letter integration tests.
6. Connect the adapter to the Stateless Runner.
