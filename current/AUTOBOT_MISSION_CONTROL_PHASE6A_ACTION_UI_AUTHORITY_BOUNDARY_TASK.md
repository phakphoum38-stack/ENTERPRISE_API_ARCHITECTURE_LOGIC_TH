# Autobot Mission Control Phase 6A — Action UI Authority Boundary Task

## Objective
Begin Phase 6 by defining the smallest safe boundary between the frozen read-only Mission Control UI and future action-oriented controls.

Phase 6A must **not implement arbitrary actions**. It defines and verifies the contract that any future action UI must follow.

## Frozen boundary
Mission Control Phases 4A–5J remain frozen and read-only.

Future action-oriented UI must be a separate presentation layer that routes every requested side effect through the existing authorities:

`UI intent → FriendOrchestrator → OwnerPolicy → ApprovalGate → execution authority → Evidence/Trace`

The UI must never become an execution authority.

## Required separation
Do not modify the meaning of existing Mission Control read-only contracts to accommodate actions.

Keep distinct:
- read-only observation;
- action intent/request;
- authorization decision;
- explicit approval;
- execution;
- evidence/trace.

A displayed action proposal is not an executed action.
A validated action request is not authorization.
Authorization is not approval.
Approval is not execution.
Execution is not evidence until authoritative trace/evidence exists.

## Action intent contract
Define a minimal versioned action-intent representation containing only what is necessary to request work.

At minimum establish:
- schema/version;
- owner/session identity;
- intent ID;
- action type from an explicit allow-list;
- bounded human-readable reason/goal;
- target reference that cannot itself encode executable code;
- requested parameters subject to strict schema validation;
- read-only/side-effect classification;
- approval requirement;
- deterministic correlation ID.

Do not accept arbitrary code, shell strings, dynamic imports, process descriptors, callbacks, scripts, browser automation instructions, or unrestricted URLs as action payloads.

## Owner and session isolation
Every action intent must be bound to the active owner/session.

Reject:
- missing owner identity;
- owner mismatch;
- cross-session reuse where the contract forbids it;
- attempts to reference another owner's EXE/application identity;
- attempts to use Mission Control navigation as an owner-switch mechanism.

The four-user / four-EXE model remains a hard security boundary.

## Authorization boundary
Action UI may request authorization through the canonical path, but it must not decide authorization itself.

`OwnerPolicy` remains authoritative.

The UI must not:
- invent permissions;
- escalate permissions;
- reinterpret denied policy as allowed;
- cache authorization across owners;
- bypass policy because a user clicked a trusted-looking control.

## Approval boundary
If an action requires approval, `ApprovalGate` remains authoritative.

The UI must:
- clearly show that approval is required;
- distinguish `PENDING`, `APPROVED`, `DENIED`, `EXPIRED`, `UNKNOWN`, and other authoritative states where supported;
- never imply approval merely because a dialog was opened;
- never treat UI confirmation alone as authoritative approval;
- never silently retry or auto-approve.

## Execution boundary
`FriendOrchestrator` remains the execution authority.

The action UI must not directly call:
- subprocess/shell;
- PowerShell/cmd;
- OS input;
- browser automation;
- MCP tools;
- arbitrary tools;
- installation/build/signing commands;
- network side-effect APIs.

The UI submits a validated intent to the canonical orchestration boundary only.

## Evidence and trace
Every executed action must eventually be attributable to authoritative trace/evidence.

The UI may display evidence/trace after receiving it from the canonical read-only projection path.

The UI must not manufacture:
- success;
- execution IDs;
- completion timestamps;
- build/release identity;
- provenance;
- approval records.

Unknown or unavailable evidence remains unknown/unavailable.

## Safety and payload bounds
Define strict bounds for:
- action-intent bytes;
- action type length/count;
- parameter count/depth;
- string lengths;
- target reference lengths;
- collection sizes.

Reject oversized or structurally suspicious payloads before they reach execution authority.

Reject secret-like fields including:
- passwords;
- API keys;
- bearer tokens;
- private keys;
- signing secrets;
- credential blobs.

## UI semantics
Future action controls must make side effects explicit.

At minimum distinguish:
- `OBSERVE` — no side effect;
- `PROPOSE` — creates an intent/request only;
- `AWAITING_AUTHORIZATION`;
- `AWAITING_APPROVAL`;
- `AUTHORIZED`;
- `APPROVED`;
- `EXECUTING`;
- `COMPLETED`;
- `FAILED`;
- `DENIED`;
- `UNKNOWN`.

Do not use color alone to communicate these states.

## Tests
Add contract tests for:
1. valid bounded action intent;
2. missing owner;
3. owner mismatch;
4. invalid action type;
5. oversized payload;
6. excessive nesting;
7. executable code injection;
8. shell/process injection;
9. callback/dynamic descriptor injection;
10. secret-like field injection;
11. authorization denied;
12. approval required;
13. approval denied/expired;
14. UI confirmation without authoritative approval;
15. direct execution attempt from UI;
16. cross-owner intent reuse;
17. evidence fabrication;
18. deterministic serialization;
19. immutable request representation;
20. preservation of frozen 4A–5J Mission Control behavior.

## Evidence artifacts
Produce:
- clean `current/AUTOBOT_MISSION_CONTROL_PHASE6A_ACTION_UI_AUTHORITY_BOUNDARY.diff`;
- machine-readable evidence containing exact base/head SHA, action-intent schema version, bounds, test results, owner-isolation results, authority mapping, and side-effect audit;
- documentation showing the action boundary and the separation from frozen Mission Control.

The `.diff` must not include itself.

## Authority invariants
- execution → `FriendOrchestrator`;
- authorization → `OwnerPolicy`;
- approval → `ApprovalGate`;
- trace/evidence → canonical runtime evidence path;
- read-only Mission Control → frozen 4A–5J contracts;
- action UI → request/presentation only;
- tests/evidence → verification only.

No new authority may be introduced.

## Workflow discipline
- No manual workflow dispatch.
- No merge.
- Do not weaken any release/build/provenance gate.
- Do not mutate protected workflow configuration.
- Do not execute real side effects merely to validate the contract.

## Completion report
Report exact base SHA, implementation HEAD SHA, changed files, action-intent schema version, bounds, tests/results, authority audit, owner isolation matrix, side-effect audit, diff SHA-256, evidence path, and PR URL.
