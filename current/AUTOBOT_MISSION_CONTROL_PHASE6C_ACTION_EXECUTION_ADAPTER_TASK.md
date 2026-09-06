# Phase 6C — Canonical Action Execution Adapter

Implement a narrow adapter from approved action requests into the existing FriendOrchestrator execution boundary.

## Requirements
- consume only validated, owner-bound, policy-authorized, approval-satisfied intents;
- call the existing orchestration authority rather than creating a new executor;
- preserve correlation ID, owner/session identity, action type, approval state, and request hash;
- reject missing/stale/conflicting authorization or approval evidence;
- prevent replay and cross-owner reuse;
- return bounded immutable execution references only;
- execution result is not fabricated; canonical runtime trace remains authoritative;
- Tool/MCP/Computer Use remain downstream boundaries and cannot be bypassed;
- no shell/process/network/OS input directly from adapter;
- no secret or credential material.

## Tests
Positive approved request, denied request, approval missing/expired, owner mismatch, stale authorization, replay, conflicting evidence, bounded output, deterministic correlation, and direct-execution bypass attempts.

## Evidence
Create clean `current/AUTOBOT_MISSION_CONTROL_PHASE6C_ACTION_EXECUTION_ADAPTER.diff` plus machine-readable evidence. Include exact base/head SHAs, authority mapping, test results and side-effect audit.

No manual dispatch, merge, or gate weakening.
