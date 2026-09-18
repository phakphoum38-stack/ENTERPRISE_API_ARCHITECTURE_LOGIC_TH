# P1-15 Cross-Partition Evidence Correlation

P1-15 adds a pure projection over existing execution-evidence bindings.

## Contract
- Correlates existing evidence bindings under one canonical mission/work/baseline identity.
- Preserves project namespace isolation established by P1-14.
- Treats partition IDs as routing metadata only.
- Requires a declared 64-character SHA-256 correlation fingerprint.
- Fails closed on lineage mismatch, missing evidence, or invalid hashes.
- Does not create an evidence store, scheduler, queue, worker, execution engine, authority path, merge path, or CI behavior.

## Scale boundary
The 10^10 federation remains logical. Correlation does not materialize 10 billion projects or evidence records in memory.

## Governance boundary
P1-15 only correlates evidence. It does not verify, certify, authorize, approve, or merge.
