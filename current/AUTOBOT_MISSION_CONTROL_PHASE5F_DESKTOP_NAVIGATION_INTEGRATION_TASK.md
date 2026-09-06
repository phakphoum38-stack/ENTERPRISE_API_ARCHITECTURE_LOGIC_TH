# Autobot Mission Control Phase 5F — Desktop Navigation and Workspace Integration Task

## Objective
Integrate Mission Control into the existing Owner Special Research OS desktop navigation without creating a second shell, second workspace authority, or parallel execution path.

## Lineage
Continue from the exact Mission Control development HEAD produced after Phase 5E. Record exact base SHA and implementation HEAD SHA in evidence. Do not silently rebase onto a moving branch.

## Scope
Add a stable desktop navigation entry/view for Mission Control inside the existing `owner_special/flutter_app` shell.

Mission Control is a **read-only observability surface**. It must consume the validated Phase 4H unified snapshot through the Phase 4I presentation adapter and Phase 5A–5E contracts.

The integration must preserve existing Research OS surfaces, especially:
- canonical workspace/chat;
- Launch Desk;
- existing shell/navigation structure;
- owner identity/session routing;
- existing desktop window lifecycle.

Mission Control must be one destination in the existing shell, not a replacement shell.

## Navigation requirements
- Add a deterministic Mission Control navigation destination.
- Use existing navigation/router/shell primitives where available.
- Preserve existing route identity and deep-link semantics where they already exist.
- Do not introduce an independent navigation authority.
- Do not make navigation itself an execution trigger.
- Do not execute refresh, tools, MCP, Computer Use, shell commands, browser actions, or OS input merely because the Mission Control route is opened.
- Opening Mission Control must be safe even when the underlying snapshot is unavailable, stale, invalid, truncated, pending, or unknown.

## Presentation contract
The Mission Control screen must render only the validated presentation model.

It may display:
- owner/session identity;
- read-only indicator;
- synchronization state;
- run/trace summary;
- timeline;
- capability health;
- evidence/provenance;
- build/release identity;
- authoritative gate status;
- truncation and uncertainty indicators.

It must not manufacture data from:
- filenames;
- timestamps without authoritative meaning;
- absence of failures;
- local UI state;
- cached values from another owner/session;
- inferred release/build identity.

## Workspace integration
Mission Control should coexist with existing workspace/chat surfaces:
- switching to Mission Control must not destroy or mutate canonical chat/workspace state;
- returning to workspace/chat must preserve the existing shell contract;
- no second Friend/Orchestrator instance may be created for Mission Control;
- no second OwnerPolicy or ApprovalGate may be created;
- Mission Control cannot bypass the existing runtime boundaries.

If shared shell state is required, use immutable/read-only projections or existing state management. Do not introduce hidden global mutable state.

## Owner isolation
The route and its view model must remain owner/session scoped:
- navigation state must not leak one owner into another;
- Mission Control must reject or discard mismatched snapshot data;
- caches, restoration state, and route parameters must not cross owner/session boundaries;
- four-user/four-EXE separation remains intact.

## UX safety
Navigation controls are not action controls.

Reject or avoid:
- buttons that directly invoke FriendOrchestrator;
- executable command strings;
- arbitrary URLs/links with side effects;
- callbacks encoded in snapshot data;
- provider response bodies exposed as executable content;
- dynamic component constructors;
- hidden background refresh/execution;
- automatic approval or policy changes.

A refresh affordance, if exposed, must route only through the Phase 5E read-only synchronization boundary.

## Failure handling
The desktop destination must explicitly represent:
- `EMPTY`
- `LOADING`
- `READY`
- `TRUNCATED`
- `PENDING`
- `FAILED`
- `UNKNOWN`
- `INVALID_SOURCE`

Do not convert uncertainty into success.
Do not hide truncation.
Do not silently substitute stale data for rejected data.

## Accessibility and desktop quality
- Provide accessible labels for navigation and status indicators.
- Keep keyboard navigation deterministic.
- Preserve focus when switching between shell destinations where practical.
- Avoid unnecessary rebuilds of unrelated workspace/chat surfaces.
- Keep Mission Control rendering bounded according to Phase 5D.
- Preserve existing window sizing/theme conventions rather than creating a parallel visual system.

## Tests / evidence
Add focused tests covering:
1. Mission Control destination appears in the existing shell;
2. route opens without execution side effects;
3. canonical workspace/chat remains intact after navigation;
4. Mission Control consumes only validated presentation data;
5. all synchronization/error states render explicitly;
6. owner mismatch is rejected;
7. owner/session restoration cannot cross boundaries;
8. no duplicate execution/authorization/approval authority is instantiated;
9. refresh, if present, routes only through read-only synchronization;
10. deterministic navigation order and stable widget keys;
11. accessibility labels/focus behavior;
12. large bounded snapshots do not rebuild unrelated shell surfaces.

Produce:
- clean `current/AUTOBOT_MISSION_CONTROL_PHASE5F_DESKTOP_NAVIGATION_INTEGRATION.diff`;
- machine-readable evidence with exact SHA lineage, changed files, tests/results, diff hash, schema/version, and authority declarations;
- documentation for route/shell integration and safety invariants.

## Authority invariants
- execution → `FriendOrchestrator`
- authorization → `OwnerPolicy`
- approval → `ApprovalGate`
- trace source → `AgentRuntime`
- snapshot/presentation → Mission Control read-only contracts
- desktop navigation → existing Research OS shell only

Mission Control navigation must never become a new execution authority.

## Workflow discipline
- No manual workflow dispatch.
- No automatic merge.
- Do not weaken existing release gates.
- Do not mutate protected gate configuration.

## Completion report
Report exact base SHA, exact HEAD SHA, files, tests/results, diff artifact + SHA-256, evidence path, route identity, owner isolation status, confirmation of no new authority, and PR URL.
