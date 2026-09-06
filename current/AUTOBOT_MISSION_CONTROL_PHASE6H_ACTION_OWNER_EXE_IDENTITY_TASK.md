# Phase 6H — Action Owner / Four-EXE Identity Binding

Bind every action request to canonical owner/application identity without creating a second routing authority.

## Requirements
- four users remain four isolated EXE/application identities;
- consume canonical Build Identity and Installed Owner Release Provenance evidence;
- action intent must carry owner/session identity and validated application identity;
- reject filename/path/title-only identity inference;
- reject missing, stale, conflicting, malformed or owner-mismatched identity evidence;
- never switch owner or EXE as an action side effect;
- no build/package/sign/install/uninstall/launch authority in UI;
- preserve identity through authorization, approval, execution and evidence correlation;
- no secrets or credentials.

## Tests
All four owner identities, cross-owner mismatch, wrong EXE, missing/stale/conflict evidence, replay, navigation, refresh and deterministic identity binding.

## Evidence
Create clean `current/AUTOBOT_MISSION_CONTROL_PHASE6H_ACTION_OWNER_EXE_IDENTITY.diff` and machine-readable evidence.

No manual dispatch, merge, or gate weakening.
