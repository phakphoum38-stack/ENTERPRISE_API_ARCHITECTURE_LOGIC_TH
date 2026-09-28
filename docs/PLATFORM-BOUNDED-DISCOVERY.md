# Platform Bounded Discovery Infrastructure

This layer extends the existing **Platform Virtual Workspace**. It does not create
another registry, queue, scheduler, memory store, runtime, or authority.

## Resolution order

```
Virtual Space
  ↓
Canonical Root
  ↓
Same-Level Peers
  ↓
Exact Match / Capability / Fingerprint
  ↓
Descend One Level
  ↓
Repeat
```

The engine must never create a resource merely because an initial lookup failed.

### Terminal states

- `FOUND_AT` — canonical existing resource found.
- `ABSENT_FROM_SCOPE` — bounded search proved absence in the selected scope.
- `AMBIGUOUS` — multiple same-level matches; HOLD.
- `ROOT_UNRESOLVED` — root is unknown; STOP.
- `TIMEOUT` — budget exhausted; return proof, do not create.
- `EMERGENCY_STOP` — safety/operator stop; preserve state and stop.

Only `ABSENT_FROM_SCOPE` permits a caller to consider creation.

## Bounded-search contract

The default discovery budget is:

- 60 seconds
- depth 32
- 100,000 nodes
- 8 workers
- 128 remote calls
- 256 concurrent admissions

These are hard bounds, not suggestions.

## Duplicate protection

Discovery checks:

1. exact identity
2. same-level name
3. capability identity
4. structural fingerprint
5. cross-space capability/fingerprint collisions

A duplicate candidate is reported; it is not deleted automatically.

## Caches and index

Positive and negative results are cached for the current registry projection.
The index is rebuildable from the canonical registry, so the index itself is not
the source of truth.

## Parallelism and backpressure

Same-level probes may execute in parallel. Admission is bounded. When the
capacity is full, discovery fails closed instead of spawning an unbounded queue.

An emergency stop cancels pending probes and prevents creation.

## Discovery proof

Every result carries:

- discovery id
- virtual space
- root
- target
- levels examined
- candidates
- nodes/peers examined
- remote calls
- cache/index hit
- latency
- reason
- evidence

This makes a discovery result auditable without reconstructing the search.

## Self-maintenance

When the canonical registry changes, the index can be rebuilt. Stale,
unreferenced resources are reported as archive candidates only; deletion remains
outside Discovery and stays under the existing authority/final-gate controls.

**Rule:** `ค้นให้เร็ว แต่ห้ามเดา และห้ามสร้างซ้ำ`.

## Internal / External boundary

Discovery uses one unified registry with two source scopes. `INTERNAL` may establish canonical system structure; `EXTERNAL` is observation-only and may correlate with the system but cannot establish system authority or a canonical root. Unknown scope is fail-closed and stops discovery.
