# P1 Functional Integration
P1-12 composes the completed P1 governance projections into one immutable,
side-effect-free integration trace.

Chain: Canonical Identity -> Independent Review Handoff -> Pre-Authority ->
Owner Authority Packet -> Owner Authority Decision.

The integration layer only correlates and validates existing projections. It
does not execute work, schedule work, create queues/workers, mutate AEOS,
grant Owner Authority, authorize merge, mutate Git, or mutate CI.

Fail-closed invariants cover lineage, review PASS, target continuity,
READY_FOR_AUTHORITY, packet digest continuity, anti-escalation, protected
baseline exclusion, acknowledgement, and trace fingerprint integrity.

APPROVE remains a recorded Owner decision only. It is not converted into
merge authorization by this layer.
