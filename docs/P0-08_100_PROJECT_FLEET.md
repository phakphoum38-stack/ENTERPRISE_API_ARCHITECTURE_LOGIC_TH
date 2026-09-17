# P0-8 — 100-Project Fleet Federation

## Purpose

Provide one bounded federation layer for up to **100 concurrent projects** while
reusing the existing Research OS Scheduler, AEOS durable work graph, queues,
workers, and execution state machines.

P0-8 is a **registry and correlation boundary**, not an execution engine.

## Boundary

```
Existing Scheduler / AEOS / Queue / Workers
                 ↑
        Continuous Supervisor
                 ↑
        P0-8 Project Fleet
                 ↑
       Canonical Identity
                 ↑
       Project 1 ... Project 100
```

The fleet does not schedule or execute work. It only records immutable project
descriptors and supervisor decision projections.

## Invariants

1. Maximum fleet size is exactly 100 project descriptors.
2. `project_id` is unique.
3. Canonical `mission_id` is unique inside the fleet.
4. Canonical `work_id` is unique inside the fleet.
5. Every project is bound to an existing `CanonicalIdentity`.
6. Supervisor decisions must match the project's canonical identity.
7. Recording a supervisor decision does not apply the action.
8. Fleet updates return new immutable snapshots; the previous snapshot remains unchanged.
9. No new scheduler, queue, worker, state machine, retry engine, or execution engine is created.
10. No authority or merge capability is granted.

## Existing infrastructure reused

- Scheduler: existing infrastructure; intentionally skipped by P0-8.
- AEOS WorkItem: remains the canonical durable work object.
- CanonicalIdentity: remains the cross-plane identity contract.
- ContinuousSupervisor: remains the decision boundary.
- Existing queues/workers/state machines: remain authoritative for execution.

## Scale model

The target is:

```
1 Fleet
  └── up to 100 FleetProject descriptors
       └── each bound to one canonical mission/work lineage
```

This avoids creating 100 schedulers or 100 queues.

## Verification boundary

P0-8 tests cover:

- capacity enforcement at 100
- duplicate project/work/mission rejection
- immutable registration/removal
- supervisor decision correlation
- fail-closed identity mismatch

Execution, scheduling, leasing, retries, authority, Git mutation, and release
are intentionally outside this module.
