# Research OS Platform Governance

Status: ACTIVE

This governance layer composes existing canonical registries, contracts, dependency graph, architecture invariants, evidence lineage, and Final Gate. It is not a second runtime, control plane, authorization authority, evidence ledger, scheduler, queue, or release authority.

## Governance loop

DISCOVER → INVENTORY → TRACE → CLASSIFY → IMPACT ANALYSIS → VALIDATE → EVIDENCE → UNIFIED FINAL GATE

## Long-term rules

1. One authority per domain; governance only records and validates.
2. Reuse existing ProjectRegistry, Workflow Engine, evidence plane, resource controls, Virtual Workspace, Control Center and Final Gate.
3. Navigation/surface tests derive from canonical sources; no hard-coded destination cardinality.
4. Unknown, missing, stale, conflicting, or mismatched evidence never becomes PASS/DONE.
5. Every governed change records affected components, contracts, risk, blast radius and required gates.
6. Evidence must be attributable; source-file existence alone is not completion.
7. FINAL_GATE remains the single release authority.

Future extensions must reuse the governance contract and Platform Graph rather than create another graph/control plane.
