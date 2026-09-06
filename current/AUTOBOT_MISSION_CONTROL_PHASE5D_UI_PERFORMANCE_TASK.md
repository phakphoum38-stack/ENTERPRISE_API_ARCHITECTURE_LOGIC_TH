# Autobot Mission Control Phase 5D — UI Performance and Bounded Rendering Task

## Objective
Keep Mission Control responsive and predictable as traces, timelines, evidence, and gate history grow.

## Requirements
- Render only bounded validated collections from the unified snapshot.
- Prefer lazy/virtualized rendering for potentially large tables/timelines.
- Avoid repeated serialization/parsing of the same snapshot during a frame.
- Keep stable keys/order for deterministic widget trees.
- Never poll or refresh by invoking runtime execution; refresh is allowed only when backed by an existing read-only data source contract.
- Keep payload and per-panel bounds visible in diagnostics.
- Handle large strings and malformed records without expensive recursive work beyond canonical limits.

## Safety
Performance optimizations must not weaken owner isolation, schema validation, provenance, gate semantics, or read-only guarantees. No caching may cross owner/session boundaries.

## Tests / evidence
Add performance-oriented widget/unit coverage for bounded large snapshots, truncation, repeated renders, owner-scoped caches, deterministic output, and malformed payload handling. Produce clean `.diff` and machine-readable evidence.

## Workflow discipline
No manual workflow dispatch. No automatic merge.