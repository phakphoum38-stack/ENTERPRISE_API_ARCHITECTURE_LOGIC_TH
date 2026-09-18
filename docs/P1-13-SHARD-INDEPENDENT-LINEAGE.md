# P1-13 Shard-Independent Lineage

This projection separates **routing metadata** from **canonical lineage**.

Canonical lineage remains:

- mission_id
- work_id
- baseline_sha

The 10^10 federation partition and slot are routing coordinates only. They
must not become a new identity namespace or execution authority.

The projection validates deterministic addressing and produces a SHA-256
lineage fingerprint from mission, work, baseline, and project identity.

No scheduler, queue, worker, execution engine, authority engine, merge path,
or CI mutation is introduced.
