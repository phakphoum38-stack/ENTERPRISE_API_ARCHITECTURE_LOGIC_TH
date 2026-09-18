# P1-11 Owner Authority Decision Acknowledgement

Records an explicit Owner Authority decision against an existing AEOS Authority Packet.

This is a correlation/evidence boundary only. It does not perform the decision.

Supported explicit decisions:

- `APPROVE`
- `REJECT`
- `HOLD`

Invariants:

- decision is tied to the exact packet digest and target SHA;
- work/mission/baseline lineage must match the canonical identity;
- protected baseline cannot be the target;
- automation cannot grant Owner Authority;
- automation cannot grant merge authorization;
- no Git ref, CI, AEOS state, or merge mutation occurs.

An `APPROVE` acknowledgement therefore means only that an explicit owner decision was recorded against the packet. Any subsequent release/merge action remains a separate governed boundary.
