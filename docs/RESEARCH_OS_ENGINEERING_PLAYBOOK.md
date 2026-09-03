# Research OS Engineering Playbook

## Purpose

Research OS is developed using the same operating model used by large enterprise software teams: decompose the product into bounded subsystems, define contracts between them, validate each layer automatically, and release only artifacts with traceable source lineage.

## 1. Decompose the product

```text
Research OS
├── Authentication
│   ├── Google
│   ├── Microsoft
│   └── GitHub
├── Unified Session
├── Friend
│   ├── Chat
│   ├── Voice
│   └── Tools
├── Calendar
│   └── phakphum-calendar
├── Windows Desktop
├── ServiceHost
├── Installer
└── Release / CI-CD
```

Each subsystem owns a clear responsibility and should not bypass another subsystem's contract.

## 2. Define contracts between subsystems

Every integration boundary should define, at minimum:

- Input and output
- Authentication/authorization
- Error model
- Timeout and retry behavior
- Version compatibility
- Health/readiness signal
- Observability/audit requirements

Canonical relationship:

```text
Auth
  ↓
Unified Session
  ↓
Friend
  ↓
Calendar Tool
  ↓
Calendar Service
  ↓
phakphum-calendar
```

## 3. Git and Pull Request discipline

Do not use `main` as a working branch for feature/fix development.

```text
main
├── feature/auth
├── feature/calendar
├── fix/windows-installer
└── fix/release-pipeline
```

Expected flow:

```text
Branch → Tests → Pull Request → CI → Review → Merge
```

## 4. CI/CD is the production assembly line

The release pipeline should make the correct sequence deterministic:

```text
Git Push
  ↓
Checkout exact source SHA
  ↓
Static Analysis
  ↓
Unit Tests
  ↓
Integration Tests
  ↓
Build
  ↓
Build Identity Gate
  ↓
ServiceHost / Runtime Gate
  ↓
Installer Build
  ↓
Install E2E
  ↓
Upgrade E2E
  ↓
Uninstall / Data Preservation E2E
  ↓
Packaged Identity Gate
  ↓
Complete Release Bundle
  ↓
Final Release
```

A failed gate stops downstream release publication.

## 5. One source of truth and strict lineage

Every distributable artifact must be traceable to an exact source commit.

```text
Canonical Source SHA
       ↓
Research OS Build
       ↓
Friend Build
       ↓
Owner EXE
       ↓
Installer
       ↓
Complete ZIP
       ↓
Release Manifest
```

Do not silently mix source revisions. A green build assembled from different, undocumented commits is not considered a valid release.

The release manifest should record at least:

- source commit SHA
- Friend source SHA
- Owner build identity
- artifact names
- SHA-256 checksums
- validation results
- build timestamp

## 6. Green means verified, not perfect

Use multiple independent validation layers:

```text
Unit Test
  ↓
Integration Test
  ↓
E2E Test
  ↓
Build Test
  ↓
Installer Test
  ↓
Upgrade Test
  ↓
Uninstall Test
  ↓
Release Test
```

A green unit test does not prove the installer works. A green build does not prove the runtime is healthy.

## 7. Observability after release

Production validation must include:

- Logs
- Metrics
- Error/crash reporting
- Latency
- Health checks
- Service readiness
- Audit trail

Example:

```text
Research OS UI       PASS
Authentication       PASS
Friend Service       FAIL
Calendar             BLOCKED
```

The system must identify the failed boundary rather than returning a generic application error.

## 8. Canonical release lineage

Research OS release architecture:

```text
MAIN
  ↓
Canonical Commit
  ↓
Research OS + Friend
  ↓
Integration Build
  ↓
Identity Gate
  ↓
ServiceHost
  ↓
Installer
  ↓
Install / Upgrade / Uninstall E2E
  ↓
Packaged Identity
  ↓
Complete ZIP + Setup.exe
  ↓
Release Manifest
  ↓
Validated Release Artifact
```

No release artifact should be published before the relevant gates pass.

## 9. Four-user / four-EXE identity rule

The Owner edition is one member of a larger identity model:

```text
4 users = 4 isolated EXE identities
```

The Owner canonical executable identity is:

```text
research_os_owner_special.exe
```

Identity validation must check the executable metadata and `OWNER_MANIFEST.json` before an installer or release artifact is considered valid.

## 10. Recommended engineering guardrails

1. Keep one canonical release workflow. Older workflows may remain only as explicitly documented secondary validation layers.
2. Eliminate hidden or stale commit pins. If a dependency is intentionally pinned, record why, when it is refreshed, and how it participates in release lineage.
3. Require artifact names to contain validation state such as `validated` when appropriate.
4. Generate a machine-readable release manifest for every final bundle.
5. Verify SHA-256 for the final distributables.
6. Add smoke tests for real Auth → Session → Friend → Calendar integration, not only mocked tests.
7. Add service readiness/health checks before launching UI E2E.
8. Add negative-path tests for timeout, retry, service unavailable, expired session, and partial sync.
9. Keep release gates fail-closed: missing evidence is a failure, not a warning.
10. Periodically audit all GitHub Actions workflows and classify them as canonical, secondary validation, development-only, or obsolete.
11. Prefer reusable workflow components once the canonical release path is stable; avoid duplicating release logic across many YAML files.
12. Treat the release manifest and artifact lineage as part of the product, not optional documentation.

## Definition of Done for a release

A release is Done only when:

- source lineage is known
- tests pass
- build identity passes
- Friend/ServiceHost readiness passes
- installer builds successfully
- install E2E passes
- upgrade E2E passes
- uninstall/data-preservation E2E passes
- packaged identity passes
- final artifacts are checksummed
- release manifest is generated
- final artifact is uploaded only after all required gates pass

This playbook is the default engineering policy for future Research OS release work unless a documented exception is approved.
