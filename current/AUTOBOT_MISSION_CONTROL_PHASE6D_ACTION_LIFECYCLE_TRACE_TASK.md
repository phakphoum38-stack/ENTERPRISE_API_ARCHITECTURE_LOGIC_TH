# Phase 6D — Action Lifecycle Trace & Evidence

Connect action requests and execution outcomes to the canonical trace/evidence path.

## Requirements
- deterministic lifecycle correlation from intent to execution to evidence;
- distinguish requested, authorized, approved, executing, completed, failed, denied, expired and unknown;
- consume authoritative runtime events rather than manufacture status;
- preserve owner/session and request identity;
- bounded trace/evidence projection;
- immutable presentation data;
- fail closed on conflicting, stale, malformed, missing or cross-owner evidence;
- never expose credentials, tokens, keys, passwords or provider bodies;
- preserve existing Mission Control 4A–5J read-only projection semantics.

## Tests
Lifecycle completeness, partial lifecycle, conflicting evidence, missing evidence, stale evidence, owner mismatch, replay, bounds, determinism and secret-like payload rejection.

## Evidence
Produce clean `current/AUTOBOT_MISSION_CONTROL_PHASE6D_ACTION_LIFECYCLE_TRACE.diff` and machine-readable evidence with exact SHAs and side-effect audit.

No manual dispatch, merge, or gate weakening.
