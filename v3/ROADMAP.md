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

## Phase 3 - Local service and user isolation

- [x] V3 local API service on loopback only
- [x] `/health`, `/v3/master`, `/v3/providers`
- [x] Windows Service host
- [x] Lifecycle and local data ownership rules
- [x] Validated `UserContext` and profile context
- [x] Per-user/profile data scopes under `users/<user-id>/profiles/<profile-id>/`
- [x] Cross-user and cross-profile isolation tests
- [x] `/v3/user` context contract with path-traversal rejection
- [x] Desktop startup probe carries user/profile context

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
- [x] Installed `/v3/user` proof for two users and multiple profiles
- [x] Installed Flutter app-to-service E2E includes `/health`, `/v3/user`, `/v3/providers`
- [x] In-place upgrade preserves isolated user/profile markers
- [x] Clean uninstall preserves isolated user/profile data while removing app/service/listener
- [x] Final candidate manifest only after all required gates pass

## Release readiness rule

A commit is release-ready only when its exact SHA passes the V3 Core, Provider Hardening, Software Factory, and Candidate workflows. Passing evidence from earlier SHAs is retained for audit but is not substituted for final exact-SHA validation.

Provider Hardening and Factory Execution are intentionally triggered by this roadmap, so the final user-isolation certification SHA receives evidence from every primary V3 validation workflow.
