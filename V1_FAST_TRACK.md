# Research OS v1.0.0 Fast-Track Plan

Status: IN PROGRESS

## Source-of-truth version

The Flutter application currently declares `0.1.0+1` in `apps/research_os_flutter/pubspec.yaml`.
Version numbers will only advance when the required gates below are met.

## Fast-track sequence

1. `0.9.0-dev.1` — feature-complete candidate
2. `0.9.0-rc.1` — release candidate after full regression gates
3. `1.0.0` — stable release after installer/release/health gates pass

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
- [ ] Create Orchestration UI
- [ ] Flutter widget tests for Agent Center orchestration flow

### Runtime and API
- [x] Stable Research OS API base
- [x] Agent API compatibility layer
- [ ] Promote Agent API entrypoint into the primary runtime/service path
- [ ] OpenAPI contract for orchestration endpoints
- [ ] Runtime smoke test for orchestration endpoints

### Desktop / delivery
- [x] Windows Flutter release build
- [x] Short-path Windows native build fix
- [x] Service Host build
- [x] Runtime Smoke pipeline
- [x] Installer build
- [x] Installer validation
- [x] Release artifact pipeline
- [x] Release compatibility gate using source run ID
- [ ] Full v1 candidate pipeline on the same target SHA

### Quality gates
- [ ] `flutter analyze` clean
- [ ] Flutter tests pass
- [ ] Agent Platform tests pass
- [ ] API tests pass
- [ ] Windows release build pass
- [ ] Installer validation pass
- [ ] Release artifact pass
- [ ] Production Health pass

## Promotion rules

### Promote to 0.9.0-dev.1 when
- Multi-Agent UI is feature complete.
- Agent orchestration API is available through the runtime used by the app.
- Analyze and unit/widget tests pass.

### Promote to 0.9.0-rc.1 when
- Windows app, service host, runtime smoke, installer, installer validation, and release pipeline all pass against one candidate SHA.
- No known release-blocking defects remain.

### Promote to 1.0.0 when
- RC passes production health and secondary web/Pages validation.
- Release artifact and verification manifest are reproducible.
- Baseline/rollback reference is recorded.

## Fast-track working rule

Bundle related implementation into larger vertical slices and run the smallest relevant CI gate first. Do not modify already-green release workflows unless a failing gate proves the workflow itself is the cause.
