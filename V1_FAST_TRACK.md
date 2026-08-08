# Research OS v1.0.0 Fast-Track Plan

Status: RELEASE CANDIDATE — `0.9.0-rc.1`

## Source-of-truth version

The Flutter application declares `0.9.0-rc.1+1` in `apps/research_os_flutter/pubspec.yaml`.
The API contract declares `0.9.0-rc.1` in `tools/research_os_api/openapi.yaml`.

RC evidence candidate SHA: `1ad63b10aa0fac3aa98173334c4394fc43487eab`.

## Fast-track sequence

1. `0.9.0-dev.1` — feature-complete candidate
2. `0.9.0-rc.1` — release candidate after full regression gates
3. `1.0.0` — stable release after final stable-release checks

## v1 scope — must complete

### Multi-Agent platform
- [x] Agent registry and capability router
- [x] Agent runtime and shared context
- [x] Multi-Agent orchestrator
- [x] Dependency delegation
- [x] Write confirmation policy
- [x] Orchestrator HTTP API
- [x] Flutter API client integration
- [x] Live Agent Center orchestration dashboard
- [x] Create Orchestration UI
- [x] Flutter widget tests for Agent Center orchestration flow

### Runtime and API
- [x] Stable Research OS API base
- [x] Agent API compatibility layer
- [x] Promote Agent API entrypoint into the primary runtime/service path
- [x] OpenAPI contract for orchestration endpoints
- [x] Runtime smoke test for orchestration endpoints

### Desktop / delivery
- [x] Windows Flutter release build
- [x] Short-path Windows native build fix
- [x] Service Host build
- [x] Runtime Smoke pipeline
- [x] Installer build
- [x] Installer validation
- [x] Release artifact pipeline
- [x] Release compatibility gate using source run ID
- [x] Full v1 candidate pipeline on the same target SHA

### Quality gates
- [x] `flutter analyze` clean
- [x] Flutter tests pass
- [x] Agent Platform tests pass
- [x] API tests pass
- [x] Windows release build pass
- [x] Installer validation pass
- [x] Release artifact pass
- [x] Production Health pass

## RC evidence

Candidate SHA: `1ad63b10aa0fac3aa98173334c4394fc43487eab`

Validated on the same candidate chain:
- Windows App and Service Host build
- Runtime Smoke
- Installer Build
- Installer Validation
- Research OS Release
- Windows compatibility gate
- Agent Platform validation
- Flutter secondary validation
- GitHub Pages deployment
- Production Health

## Promotion rules

### Promote to 0.9.0-dev.1 when
- Multi-Agent UI is feature complete.
- Agent orchestration API is available through the runtime used by the app.
- Analyze and unit/widget tests pass.

### Promote to 0.9.0-rc.1 when
- Windows app, service host, runtime smoke, installer, installer validation, and release pipeline all pass against one candidate SHA.
- No known release-blocking defects remain.

Status: satisfied by candidate SHA `1ad63b10aa0fac3aa98173334c4394fc43487eab`.

### Promote to 1.0.0 when
- RC passes production health and secondary web/Pages validation.
- Release artifact and verification manifest are reproducible.
- Baseline reference is recorded.

Production health and secondary validation are green for the RC candidate. Reproducibility and baseline evidence remain the final stable-release checks.

## Fast-track working rule

Bundle related implementation into larger vertical slices and run the smallest relevant CI gate first. Do not modify already-green release workflows unless a failing gate proves the workflow itself is the cause.
