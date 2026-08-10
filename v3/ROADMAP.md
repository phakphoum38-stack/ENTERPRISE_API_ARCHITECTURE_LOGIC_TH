# V3 Clean Roadmap

## Phase 1 - Core foundation

- [x] Clean branch from `main`
- [x] Adaptive Brain Core: 1^3 / 3^3 / 6^3 / 6^6
- [x] Unified Master Orchestrator
- [x] Safe Provider Registry
- [x] Software Factory plan
- [x] Stable service-facing contracts
- [x] Unit tests and smoke test
- [x] Incremental CI evidence

## Phase 2 - Provider execution

- [x] OpenAI-compatible adapter behind a strict interface
- [x] Provider readiness/connectivity probes
- [x] Secret source abstraction for environment-backed credentials
- [x] OS-native secret store source (Windows Credential Manager)
- [x] Retry, timeout, circuit breaker, and provider fallback policy

## Phase 3 - Local service

- [x] V3 local API service on loopback only
- [x] `/health`, `/v3/master`, `/v3/providers`
- [x] Windows Service host
- [x] Lifecycle and local data ownership rules

## Phase 4 - Desktop app

- [x] Flutter shell consuming V3 contracts only
- [x] Startup app-to-service probe
- [x] Chat/conversation shell and side navigation
- [x] Provider/settings status UI without exposing secrets
- [x] Windows EXE + real app-to-service E2E evidence

## Phase 5 - Software Factory execution

- [x] Master -> Factory -> Team -> Tests -> Release execution engine
- [x] Adaptive allocation; never pre-spawn maximum capacity
- [x] Incremental evidence per stage and reproducible release inputs

## Phase 6 - Installer and candidate

- [x] One Windows installer
- [x] Clean install validation
- [x] App-to-service E2E
- [x] In-place upgrade + data preservation
- [x] Clean uninstall + service cleanup
- [x] Final candidate manifest only after all required gates pass

## Release readiness rule

A commit is release-ready only when its exact SHA passes the V3 Core, Provider Hardening, Software Factory, and Candidate workflows. Passing evidence from earlier SHAs is retained for audit but is not substituted for final exact-SHA validation.

Provider Hardening is intentionally triggered by final V3 architecture/roadmap changes as well as provider-code changes, so a final documentation-only certification commit can still produce provider evidence for the exact release SHA.
