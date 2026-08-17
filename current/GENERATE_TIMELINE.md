# Generate Timeline — Canonical

สถานะ: ACTIVE
Canonical Master: `.github/workflows/owner-special-friend.yml`

## Canonical execution path

```text
T0 Foundation
  ↓
T1 Owner/Friend Master
  ↓
T2 V3/Core validation
  ↓
T3 Desktop Build
  ↓
T4 Installer Build
  ↓
T5 Installer Validation
  ↓
T6 Owner Bundle
  ↓
T7 Final Release
  ↓
T8 SHA256 + Evidence
  ↓
T9 Cleanup
  ↓
STOP
```

## Current workflow roles

### Canonical build/release path
- `owner-special-friend.yml` — Master pipeline. It contains Friend validation, Desktop build, Installer build, Installer validation, and Owner Bundle composition.
- `release.yml` — release/publishing stage; must consume an already validated final result rather than create a parallel build.

### V3 / execution stages
- `v3-clean-core.yml`
- `v3-provider-hardening.yml`
- `v3-factory-execution.yml`
- `v3-candidate.yml`

These are supporting V3 stages. They must not create a competing Final artifact.

### Windows / source / build support
- `research-os-windows-artifact.yml`
- `research-os-windows-source-bundle.yml`
- `research-os-build-ready-source.yml`
- `artifacts-build.yml`

These are build/support artifacts. Prefer consumption by the canonical path; do not duplicate Final output.

### Gates / evidence
- `research-os-performance-gate.yml` — secondary performance gate; triggered from Windows Desktop completion and does not become a second Final pipeline.
- `research-os-unified-10x10-gate.yml` — exact-SHA Unified 10×10 validation gate.
- `ci-lite.yml`
- `file-audit-v6x6.yml`
- `research-os-chat-shell-check.yml`
- `research-os-full-chat-ai-check.yml`

These are validation/evidence stages unless proven otherwise by dependency inspection.

### Platform-specific
- `owner-special-ios-ipa.yml`
- `research-os-ios-ipa.yml`

Platform-specific outputs remain separate and must not duplicate the Windows/Owner Final artifact.

### Candidate / trigger / smoke
- `candidate.yml`
- `candidate-trigger.yml`
- `browser-use-cloud-smoke.yml`

These remain non-canonical until dependency inspection proves they are a required continuation of the canonical path.

## Generate rules

1. One capability → one canonical workflow.
2. If an equivalent workflow already exists, do not generate another one.
3. Final artifact exists and is valid → STOP.
4. Intermediate artifacts are retained only while they are dependencies for a later stage.
5. Final output is kept as one result per canonical build lineage.
6. A new Generate is allowed only when the required artifact has expired or is genuinely unavailable.
7. When regeneration is required, regenerate only the missing/expired artifact; do not rerun the entire pipeline unnecessarily.
8. Every Final must retain lineage: source/commit → build → validation → final → SHA256/evidence.
9. A newly added workflow must first be mapped to this timeline. If it is a new stage, append it; if it duplicates an existing stage, do not add it.
10. Cleanup must never delete an artifact that is still a dependency of the current run.

## Current verified implementation detail

`owner-special-friend.yml` already chains:

`friend-complete → owner-desktop → owner-installer-build → owner-installer-validation → owner-bundle`

The Desktop artifact feeds Installer Build; the raw Setup artifact feeds Installer Validation; the validated Setup artifact feeds Owner Bundle. Therefore these intermediate artifacts must not be deleted before the consuming stage completes.

## STOP condition

After Final Release + SHA256/Evidence is valid, no further Generate/Build should occur for the same lineage until an artifact expires or becomes unavailable.
