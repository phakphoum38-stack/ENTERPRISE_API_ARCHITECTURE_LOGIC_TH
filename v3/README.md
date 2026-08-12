# Research OS V3 Clean

This directory is the clean rebuild line for Research OS V3.

## Goals

- One Unified Master Orchestrator as the single coordination authority.
- Adaptive hierarchy that scales by workload instead of spawning maximum capacity by default.
- Explicit scale profiles for `1^3`, `3^3`, `6^3`, and `6^6`.
- Provider adapters that expose capability/status metadata but never provider secrets.
- A deterministic Software Factory plan: Master -> Factory -> Team -> Tests -> Release.
- App/Service contracts separated from implementation so Flutter, Windows Service, and API can evolve independently.
- Incremental evidence: a stage records success as soon as it succeeds; final candidate status is only `passed` after every required gate passes.

## Layout

- `research_os_v3/brain.py` - adaptive scale selection.
- `research_os_v3/orchestrator.py` - Unified Master Orchestrator.
- `research_os_v3/providers.py` - provider adapter and safe provider registry.
- `research_os_v3/factory.py` - software factory planning.
- `research_os_v3/contracts.py` - stable service-facing status contracts.
- `tests/` - stdlib unit tests for the clean core.
- `scripts/smoke.py` - zero-dependency smoke check.

## Current phase

Phase 1: clean foundation and executable core logic. Existing V3 code remains untouched and acts only as a migration/reference source.
