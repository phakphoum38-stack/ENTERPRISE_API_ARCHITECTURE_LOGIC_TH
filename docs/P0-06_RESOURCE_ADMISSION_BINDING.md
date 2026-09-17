# P0-6 Resource / Admission Binding

Resource control remains the authoritative admission/quota/accounting plane. P0-6 adds only an immutable correlation adapter:

`request_id → admission_id → canonical mission/work/task/run/attempt`

The adapter does not reserve quota, route providers, record usage, or replace `ResourceControlPlane`.

`binding_hash` is deterministic integrity for the correlation record. It is not authorization and does not prove subject truth.

Lineage mismatch fails closed.
