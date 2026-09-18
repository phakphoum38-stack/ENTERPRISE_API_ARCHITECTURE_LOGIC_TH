# P1-16 Evidence Partition Consistency

Validates evidence bindings remain consistent across logical partitions without changing execution or governance.

## Boundary
- Existing evidence bindings only.
- Canonical mission/work/baseline lineage remains authoritative.
- Deterministic SHA-256 projection metadata.
- Fail-closed on invalid lineage or hashes.
- No new scheduler, queue, worker, execution engine, authority, merge path, storage layer, or CI behavior.
