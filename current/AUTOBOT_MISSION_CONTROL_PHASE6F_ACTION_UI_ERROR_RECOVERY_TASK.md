# Phase 6F — Action UI Error & Recovery Boundary

Define safe recovery for failed, denied, expired, unknown and interrupted action requests.

## Requirements
- preserve authoritative failure/denial semantics;
- distinguish retryable from non-retryable only using canonical authority/evidence;
- no blind retry;
- no retry across owner/session boundaries;
- replay protection and request identity preservation;
- recovery creates a new intent when policy requires a new request, never mutates an executed request into a different action;
- unknown remains unknown;
- interrupted execution cannot be displayed as completed without authoritative evidence;
- no side effects from rendering or refresh;
- bounded diagnostics with no secrets/provider bodies.

## Tests
Failure, denial, expiry, unknown, interruption, replay, stale request, owner mismatch, retry classification, new-intent semantics, bounded diagnostics and no-side-effect recovery.

## Evidence
Create clean `current/AUTOBOT_MISSION_CONTROL_PHASE6F_ACTION_UI_ERROR_RECOVERY.diff` and machine-readable evidence.

No manual dispatch, merge, or gate weakening.
