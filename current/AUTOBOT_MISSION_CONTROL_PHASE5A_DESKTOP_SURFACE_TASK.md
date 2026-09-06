# Autobot Mission Control Phase 5A — Desktop Surface Task

## Objective
Begin Phase 5 by adding the real Mission Control desktop surface to the existing Owner Special Research OS Flutter shell, consuming the frozen Phase 4 unified projection.

## Source of truth
- UI input: frozen Phase 4H unified snapshot through the Phase 4I presentation adapter.
- UI validation: existing Mission Control UI schema validator.
- Runtime authority remains unchanged: FriendOrchestrator / OwnerPolicy / ApprovalGate.
- Do not duplicate trace, timeline, health, evidence, gate, build identity, or owner-policy engines.

## UX requirements
Provide a clear dashboard with:
- current owner identity
- system/read-only state
- run/trace summary
- timeline
- capability health
- evidence/provenance summary
- build/release identity
- authoritative gate status
- explicit PASS/FAIL/PENDING/UNKNOWN/truncated/invalid states

The surface should remain understandable when data is empty or partially unavailable. Do not hide uncertainty behind friendly UI language.

## Safety boundary
Widgets/controllers are presentation-only. No button, gesture, lifecycle callback, timer, navigation hook, or provider adapter may execute a tool, shell command, process, workflow, MCP action, Computer Use action, browser action, Windows input, build/install/release operation, approval, authorization, policy mutation, or network side effect.

## Bounds
Respect snapshot bounds and avoid unbounded widget trees. Large tables/timelines must remain truncated according to canonical metadata.

## Tests
Add widget tests for all panels, empty state, failure state, pending/unknown, truncation, owner mismatch, malformed snapshot, deterministic rendering, and proof that UI interaction cannot invoke execution authority.

## Evidence / diff
Create `current/AUTOBOT_MISSION_CONTROL_PHASE5A_DESKTOP_SURFACE.diff` and machine-readable evidence. Record exact lineage, files, tests, schema versions, bounds, and authority audit.

## Workflow discipline
Do not manually dispatch workflows. Do not merge automatically. Normal CI is verification and merge remains owner-controlled.