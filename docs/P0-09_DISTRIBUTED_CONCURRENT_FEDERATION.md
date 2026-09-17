# P0-9 — Distributed / Concurrent Federation

## Purpose

Add the coordination boundary required for concurrent operation of the
P0-8 fleet without creating another scheduler or execution system.

P0-9 models:

- bounded per-project concurrency
- immutable ownership/claim metadata
- epoch fencing
- stale-claim rejection
- canonical identity correlation

## Boundary

```
Existing Scheduler / AEOS / Queue / Lease Adapter
                    ↑
          P0-9 Coordination Boundary
                    ↑
              P0-8 Fleet
                    ↑
        Canonical Identity Federation
```

P0-9 does **not** execute the operation represented by a claim or slot.

## Invariants

1. A project cannot exceed its declared concurrency bound.
2. Slot acquisition/release returns immutable snapshots.
3. A coordination claim is bound to canonical project identity.
4. A claim is valid only while active and at the expected epoch.
5. A stale epoch fails closed.
6. An inactive claim fails closed.
7. A newer epoch fences the previous epoch.
8. A foreign canonical identity cannot claim another project.
9. No Scheduler, Queue, Worker, State Machine, or Execution Engine is created.
10. No authority, merge, Git mutation, or release capability is created.

## Why epoch fencing

Concurrent systems can have delayed/stale actors. An old actor must not be
accepted merely because it still possesses an otherwise valid identifier.

The epoch therefore forms a lightweight fencing boundary:

```
epoch 1  → stale after epoch 2 exists
epoch 2  → current
epoch 3  → fences epoch 2
```

The actual infrastructure lease remains authoritative. This module only
provides metadata that an existing adapter can validate.

## Verification

Tests cover:

- bounded concurrency
- immutable slot accounting
- active claim validation
- stale claim rejection
- inactive claim rejection
- epoch fencing
- foreign identity rejection

No workflow is executed by P0-9.
