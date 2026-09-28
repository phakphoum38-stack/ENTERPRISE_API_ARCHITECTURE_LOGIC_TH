# Research OS System Qualification

Research OS is qualified as one shared platform for 100 projects, not as a collection of independent project runtimes.

## Qualification boundary

- complete system baseline and requirement traceability
- platform architecture integrity
- shared execution and evidence planes
- 100-project scale
- failure, recovery, replay and reconciliation
- authorization and Owner boundary
- Windows / Web / iOS surface integration
- unified Windows distribution
- provenance and evidence
- M.2 descriptive audit
- AEOS assurance
- the existing Unified Final Gate

## Authority boundary

This is a qualification contract only.

- M.2 describes and indexes the repository; it is not release authority.
- AEOS provides assurance evidence; it is not release authority.
- Unified Final Gate remains the single release authority.
- External merge remains outside the contract.

## Fail-closed rules

Unknown is not pass. Deferred is not done. Missing evidence, SHA mismatch, navigation drift, cross-project isolation failure, resource overwrite, M.2 integrity failure, or AEOS non-pass stops qualification.

## One-round completion

MAIN -> inventory -> gap matrix -> implement missing -> integrate -> verify -> assure -> Unified Final Gate -> merge -> MAIN

No second release authority, project-specific runtime, project-specific queue, or project-specific evidence ledger is introduced.
