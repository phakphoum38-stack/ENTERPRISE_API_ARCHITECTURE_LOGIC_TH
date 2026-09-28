# Research OS Platform Production Hardening

This capability completes the platform boundary around 100-project operation. It is a validation and contract layer over the existing execution, queue, runner, resource-governance, evidence, and distribution components.

## Coverage

- **100-project scale:** the existing shared execution/evidence planes remain the single platform path; scale levels are 10/20/50/100.
- **Failure and recovery:** runner failure, retry exhaustion, lease expiry, stale ACK, explicit timeout, drain/cancellation admission, and resource-conflict rejection.
- **Evidence and provenance:** exact source SHA, project identity, correlation identity, terminal lifecycle state, stale-SHA rejection, and cross-project lineage rejection.
- **Unified distribution:** the existing Phase E Windows distribution remains authoritative and is checked as the single package boundary for the application, Python, tools, platform, assurance, Owner Special, workflow tooling, Universal Runner, and installer.
- **Production readiness:** contract anchors, scale invariants, failure/recovery proof, evidence isolation, distribution authority, and the existing Final Gate are evaluated together.

## Authority

This capability does not create a second runtime, scheduler, queue, authorization authority, evidence ledger, or release authority.

The existing Unified Final Gate remains the only release authority. The Owner authorization boundary remains authoritative. Distribution and validation code cannot grant entitlement or release software.

## Important semantics

`UNKNOWN`, `SKIPPED`, and `DEFERRED` are not successful release evidence.

A stale queue lease cannot be ACKed. Retry exhaustion is terminal failure rather than an implicit success. A resource version conflict is rejected and must use the existing release/reconcile path. Evidence is project-bound and source-SHA-bound.

## Proof entrypoints

- `tools/platform_production_hardening.py`
- `tools/test_platform_production_hardening.py`
- `current/RESEARCH_OS_PLATFORM_PRODUCTION_HARDENING_CONTRACT.json`

The Unified Final Gate executes the production-hardening tests alongside the existing platform, project-scale, lifecycle, distribution, and surface checks.