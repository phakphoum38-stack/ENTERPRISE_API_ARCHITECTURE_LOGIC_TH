# Research OS — Resource Version & Conflict Contract

Status: ACTIVE

## Invariant

Every mutable resource has a durable current version and content SHA head. A mutation is valid only when both values supplied by the caller match the current head.

## Stale mutation

If either value differs:
1. UPDATE is rejected atomically.
2. The execution stops; it does not retry the write against the competing version.
3. Resources held by the rejected execution are released.
4. Delivery is acknowledged or reconciled according to delivery policy.
5. Conflict evidence records expected and actual identity.
6. The competing version is never overwritten.

## Version branching

Historical versions are immutable. An alternate version may branch from a historical parent without moving the current head.

## Integration boundary

ResourceVersionStore is the write concurrency boundary. Workflow runners, Code Writer, Brain tools, and other mutating tools must pass expected version and SHA through this boundary rather than writing resources directly.

The existing queue and event-delivery layers remain responsible for leases and delivery semantics. This module does not create a second queue or event bus.

## Required evidence

Conflict evidence includes resource ID, expected version/SHA, actual version/SHA, rejection action, stop/release/reconcile disposition, and immutable conflict ID.

The unrelated Flutter CI failures remain deferred by the outstanding-work plan.
