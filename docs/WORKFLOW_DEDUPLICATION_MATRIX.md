# GitHub Actions Workflow Deduplication Matrix

Baseline: `main` @ `a06f0b7`

This matrix classifies workflows by release responsibility. A workflow is not retired solely because its name overlaps another one; equivalent coverage and artifact evidence must be proven first.

| Workflow family | Canonical workflows | Coverage | Trigger/evidence | Decision |
|---|---|---|---|---|
| PR/main final validation | `research-os-final-gate.yml` | Python compile, full V3 tests, recovery evidence, Flutter Windows validation | PR to `main`; exact checkout in job | canonical release gate |
| Exact-SHA Windows candidate | `candidate.yml` | Immutable checkout, V3/API tests, Flutter app, ServiceHost, installer and runtime smoke | manual dispatch with `target_sha`; candidate manifest | retain as release candidate gate |
| V3 candidate | `v3-candidate.yml` | V3 candidate packaging/validation | push/manual workflow | review overlap with `candidate.yml`; retain until equivalent coverage is proven |
| V3 core | `v3-clean-core.yml` | V3 core compile, unit and service checks | V3 branch/manual | specialized V3 development gate |
| V3 provider | `v3-provider-hardening.yml` | provider retry, timeout, fallback and resilience | V3 branch/manual | retain specialized provider coverage |
| V3 factory | `v3-factory-execution.yml` | bounded factory execution and stage evidence | V3 branch/manual | retain specialized factory coverage |
| V3 runtime hardening | `v3.4-dlq-replay-ci.yml`, `v3.5-worker-pool-ci.yml`, `v3.5-worker-performance.yml` | DLQ/replay, worker pool, performance and recovery | feature branches/PR/manual | retain; distinct runtime risk domains |
| V3 event store | `v3-runtime-event-store-ci.yml` | Durable events, queue outbox, state projection and metrics | PR to `main`/manual | retain specialized runtime contract gate |
| V3 integrity | `v3.5-pr-integrity.yml` | PR/source integrity controls | PR/manual | retain security/integrity gate |
| Unified runtime evidence | `research-os-unified-10x10-gate.yml` | exact-SHA 10x10 runtime evidence | push/PR/manual | retain until final gate consumes equivalent evidence |
| Research OS API/application checks | `research-os-gate.yml`, `research-os-completion-validation.yml`, `research-os-chat-shell-check.yml`, `research-os-full-chat-ai-check.yml` | API, completion, chat shell and AI behavior | push/PR/manual | consolidate overlapping API/chat checks after coverage comparison |
| Evidence and quality | `research-os-evidence-lineage.yml`, `research-os-performance-gate.yml`, `file-audit-v6x6.yml` | lineage, performance and repository audit | push/workflow-run/manual | retain distinct evidence domains |
| Windows artifacts | `research-os-windows-artifact.yml`, `research-os-v3-windows-download.yml`, `research-os-windows-source-bundle.yml`, `research-os-build-ready-source.yml` | binary, download, source bundle and build-ready archives | push/manual | retain artifact-specific outputs; avoid duplicate build steps where possible |
| iOS artifacts | `research-os-ios-ipa.yml`, `owner-special-ios-ipa.yml` | Research OS and Owner Special iOS packages | push/PR/manual | retain; separate products |
| Owner Special | `owner-special-friend.yml`, `generated-owner-evidence.yml` | Friend desktop/service and evidence | push/PR/manual | retain specialized product boundary |
| Branding/assets | `research-os-branding-gate.yml`, `gui-asset-validation.yml` | branding and GUI asset checks | push/PR/manual | compare shared asset checks before consolidation |
| GUI/UX validation | `gui-ux-validation.yml` | Flutter dependencies, analyze and complete widget test suite without installer build | PR to `main`/manual | retain as pre-release UI gate |
| Generate orchestration | `generate-orchestrator.yml`, `generate-orchestrator-hardening.yml` | generation contract and hardening | PR/push/manual | retain hardening; remove duplicate basic checks only after equivalence proof |
| General CI | `ci-lite.yml`, `assistant-core-ci.yml`, `assistant-mesh-30.yml`, `artifacts-build.yml`, `release.yml` | repository-wide or assistant/artifact/release checks | varied/manual | classify by owning product; do not merge unrelated domains |

## Safe consolidation candidates

1. Build one shared Python/API test action reused by `research-os-final-gate.yml`, `candidate.yml`, and V3 gates.
2. Compare `research-os-gate.yml`, completion validation, chat shell and full chat/AI paths; retain only checks that protect distinct contracts.
3. Compare artifact packaging steps while preserving separate binary/source/iOS outputs.
4. Make the final gate consume or link specialized evidence rather than rerunning identical checks.

## Do not retire yet

- `candidate.yml`: it proves immutable candidate identity and Windows installer/runtime behavior.
- `v3.4` and `v3.5` workflows: their DLQ, worker, recovery and performance contracts are distinct.
- Owner Special and iOS workflows: they validate different products/platforms.
- `file-audit-v6x6.yml` and integrity workflows: governance/security coverage is not interchangeable with functional tests.

## Release decision

`research-os-final-gate.yml` is the canonical PR/main validation gate. `candidate.yml` is the canonical exact-SHA Windows release gate. Specialized workflows remain required evidence providers until a future release gate demonstrates equivalent coverage without duplicated execution.
