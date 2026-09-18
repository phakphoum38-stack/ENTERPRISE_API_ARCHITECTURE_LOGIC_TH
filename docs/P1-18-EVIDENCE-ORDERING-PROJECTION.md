# P1-18 Evidence Ordering Projection

Provides deterministic evidence ordering for correlation and audit consumers.

## Boundary
- Existing evidence bindings only.
- Canonical mission/work/baseline lineage remains authoritative.
- Deterministic SHA-256 projection metadata.
- Fail-closed on invalid lineage or hashes.
- No new scheduler, queue, worker, execution engine, authority, merge path, storage layer, or CI behavior.
