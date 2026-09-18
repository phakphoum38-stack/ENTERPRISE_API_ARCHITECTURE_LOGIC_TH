# P1-17 Evidence Deduplication Projection

Projects deterministic duplicate detection for existing evidence IDs and binding hashes.

## Boundary
- Existing evidence bindings only.
- Canonical mission/work/baseline lineage remains authoritative.
- Deterministic SHA-256 projection metadata.
- Fail-closed on invalid lineage or hashes.
- No new scheduler, queue, worker, execution engine, authority, merge path, storage layer, or CI behavior.
