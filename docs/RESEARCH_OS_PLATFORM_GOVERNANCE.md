# Research OS Platform Governance

Status: ACTIVE

This is the governance layer for a growing Research OS platform. It composes existing canonical registries and validators; it is **not** a second runtime, control plane, authorization authority, evidence ledger, scheduler, queue, or release authority.

## Canonical sources

- Platform Virtual Workspace contract + registry
- Architecture Invariants
- Platform Graph
- Product Surface Inventory
- Canonical Navigation Registry
- Unified Final Gate

## Governance loop

```text
DISCOVER
  ↓
INVENTORY
  ↓
TRACE
  ↓
CLASSIFY
  ↓
IMPACT ANALYSIS
  ↓
VALIDATE
  ↓
EVIDENCE
  ↓
UNIFIED FINAL GATE
```

## Rules

1. **One authority per domain.** Governance records who/what is canonical; it does not become the authority.
2. **No duplicate control plane.** Existing ProjectRegistry, Workflow Engine, evidence plane, resource controls, Virtual Workspace, Control Center and Final Gate remain authoritative in their domains.
3. **No hard-coded surface counts.** Surface tests derive from the canonical registry.
4. **Unknown is not pass/done.** Unknown, missing, stale, conflicting, or mismatched evidence remains non-passing.
5. **Change impact is explicit.** A change records affected components, contracts, risk, blast radius and required gates.
6. **Evidence is attributable.** A component is not complete merely because its source file exists.
7. **Release remains human/governed.** FINAL_GATE remains the single release authority.

## Long-term control

The governance validator is deliberately bounded. It checks integrity of the canonical sources and cross-source consistency. It does not infer authority from UI, confidence, generated text, or an observation.

Future governance extensions must reuse this contract and the existing Platform Graph rather than creating another graph/control plane.
