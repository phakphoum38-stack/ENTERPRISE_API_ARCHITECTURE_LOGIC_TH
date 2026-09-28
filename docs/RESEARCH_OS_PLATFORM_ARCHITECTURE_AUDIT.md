# Research OS Platform Architecture Audit

This is the single platform-level reconciliation layer for the existing Research OS Platform.

It does not create a second runtime, scheduler, queue, authorization service, evidence ledger, navigation registry, or release authority.

## Platform domains

- Platform Core: identity, capability, authorization, workflow, event/queue, stateless runner, evidence/provenance, assurance.
- Control Plane: navigation, project identity, Control Center, governance, Owner.
- Execution Plane: shared workflow/event queue/stateless runner, universal runner, runner installation, scheduling boundary.
- Governance: defect, schedule, risk, change-impact, memory fabric.
- Product Surfaces: Windows, Web, iOS through the shared navigation/product-surface model.
- Scale: shared core for real project definitions at 10/20/50/100 project levels.
- Distribution: the unified Windows distribution boundary and existing Phase E contract.

## Authority model

The audit is descriptive and validating only. It does not execute, authorize, approve, merge, or release.

The Unified Final Gate remains the single release authority.

M.2 remains the descriptive repository-wide audit/index and graph. This audit complements M.2 by validating the declared platform component topology and proof bindings in one place.

## Fail-closed checks

The validator requires canonical platform anchors, complete component inventory coverage, ACTIVE lifecycle, contract/test/evidence/gate bindings, platform authority rules, and explicit Unified Final Gate binding.

Run:
- `python tools/validate_research_os_platform_architecture.py`
- `python -m unittest tools.test_validate_research_os_platform_architecture -v`

This is a platform architecture integrity check. It does not claim that every implementation bug or deferred UI test is resolved.
