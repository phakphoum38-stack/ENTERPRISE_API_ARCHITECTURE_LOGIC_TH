# Phase 6E — Action UI Confirmation Safety

Implement safe presentation for side-effecting action requests.

## Requirements
- explicit side-effect label;
- clear action type, owner, target and bounded parameters;
- show authoritative policy/approval state;
- UI confirmation is never equivalent to ApprovalGate approval;
- destructive/high-impact actions require the canonical approval path where applicable;
- no hidden actions on navigation, rendering, focus, timers or refresh;
- no auto-submit, auto-approve or retry;
- keyboard/accessibility semantics must preserve the same safety boundary;
- reject dynamic commands, callbacks, URLs, scripts, shell fragments and arbitrary component descriptors;
- preserve four-user/four-EXE identity separation.

## Tests
Confirmation without approval, double-click/replay, keyboard activation, owner mismatch, stale request, navigation/rendering side effects, malicious payloads, accessibility semantics and deterministic state transitions.

## Evidence
Create clean `current/AUTOBOT_MISSION_CONTROL_PHASE6E_ACTION_UI_CONFIRMATION_SAFETY.diff` and machine-readable evidence.

No manual dispatch, merge, or gate weakening.
