# Phase 6I — Action UI End-to-End Contract

Prove the complete controlled action path without giving the UI execution authority.

## Contract
`Desktop Action UI → ActionIntent Validator → FriendOrchestrator → OwnerPolicy → ApprovalGate → canonical execution boundary → AgentRuntime Trace/Evidence → read-only Mission Control projection`

## Requirements
- golden fixtures for safe approved and denied flows;
- exact owner/session/application identity;
- deterministic request correlation;
- explicit authorization and approval states;
- no UI-side execution;
- no direct Tool/MCP/Computer Use/OS input;
- evidence must be authoritative;
- failures, unknowns, conflicts, stale evidence and truncation remain explicit;
- unrelated workspace/chat/Launch Desk behavior remains unchanged;
- no hidden timers/listeners or background side effects;
- preserve 4A–5J freeze invariants.

## Tests
Realistic Flutter integration where feasible, Python contract tests, approved/denied/expired/unknown paths, four-owner isolation, replay, injection, malformed/oversized requests, evidence correlation and side-effect audit.

## Evidence
Create clean `current/AUTOBOT_MISSION_CONTROL_PHASE6I_ACTION_UI_E2E_CONTRACT.diff` and machine-readable evidence with exact SHAs and results.

No manual dispatch, merge, or gate weakening.
