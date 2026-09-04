# Runner Registration + Health

## Purpose

Provide a control-plane registry for a stateless runner fleet without moving job state into the runners.

## Lifecycle

```text
REGISTER
   |
   v
 ONLINE <---- HEARTBEAT
   |
   +----> DRAINING
   |
   +----> STALE
```

## Semantics

- Registration is idempotent by `runner_id`.
- Heartbeat marks a runner online and updates its last-seen timestamp.
- Health scanning marks runners `STALE` after the configured timeout.
- Draining runners remain registered but are excluded from healthy scheduling candidates.
- Capabilities allow future routing such as `python`, `node`, `gpu`, or tenant-specific execution classes.

## Production boundary

The reference registry is process-local and exists to validate semantics. Production will require durable/shared state, TTL/lease behavior, authentication, authorization, and scheduler integration.
