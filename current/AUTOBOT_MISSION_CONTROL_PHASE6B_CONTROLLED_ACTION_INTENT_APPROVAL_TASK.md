# Phase 6B — Controlled Action Intent & Approval Flow

Implement the minimal controlled action-request flow defined by Phase 6A.

## Contract
`UI → validated ActionIntent → FriendOrchestrator → OwnerPolicy → ApprovalGate → execution → Evidence/Trace`

The UI must never execute, authorize, approve, or mutate policy.

## Requirements
- versioned action-intent schema;
- exact owner/session binding;
- explicit action allow-list;
- bounded target and parameters;
- immutable request representation;
- policy decision delegated to OwnerPolicy;
- approval delegated to ApprovalGate;
- execution delegated to FriendOrchestrator;
- authoritative result/evidence only from runtime;
- explicit states: PENDING, AUTHORIZED, APPROVED, DENIED, EXPIRED, EXECUTING, COMPLETED, FAILED, UNKNOWN;
- fail closed on missing/mismatched owner, malformed payload, policy conflict, approval conflict, stale request, or unknown authority state;
- no automatic retry or implicit approval;
- no direct Tool/MCP/Computer Use/OS execution from UI;
- no credentials, tokens, keys, passwords, or provider response bodies.

## Tests
Cover valid flow, denied policy, approval-required, approval denied/expired, owner mismatch, stale request, malformed request, duplicate/replay request, deterministic serialization, secret injection, direct-execution attempt, and preservation of frozen Mission Control 4A–5J behavior.

## Evidence
Produce a clean `current/AUTOBOT_MISSION_CONTROL_PHASE6B_CONTROLLED_ACTION_INTENT_APPROVAL.diff` and machine-readable evidence with exact SHAs, schema, bounds, authority mapping, tests, and side-effect audit. The diff must not include itself.

## Discipline
No manual workflow dispatch, no merge, no gate weakening, no protected workflow mutation, and no real side effects during contract validation.
