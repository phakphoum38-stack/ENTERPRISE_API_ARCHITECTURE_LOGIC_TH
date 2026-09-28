# Autobot Mission Control Phase 4K — Owner Routing and Session Isolation Task

## Objective
Harden the desktop Mission Control surface so each Research OS user/session receives only its own validated projection, while preserving the existing four-user / four-EXE separation model.

## Required behavior
- Treat `owner_id` as a hard security boundary, not a display label.
- Route UI state from the authenticated/current owner context into the read-only Mission Control snapshot.
- Fail closed when owner identity is missing, mismatched, ambiguous, stale, or changed during a view lifecycle.
- Do not merge snapshots across owners, sessions, installations, or executable identities.
- Preserve deterministic ordering and explicit empty/invalid states.
- Never use filenames or process names alone as proof of owner identity.
- Reuse canonical OwnerPolicy/Build Identity/Installed Owner Provenance evidence; do not create a parallel authorization system.

## Four-EXE invariant
The Owner Special executable must remain distinct from the other user executables. Mission Control may display build/release identity only from canonical evidence and must never select or replace an executable, installer, package, service, or release.

## Forbidden operations
No privilege escalation, authorization decisions, approval creation, policy mutation, process launching, executable switching, installer execution, service control, network side effects, credentials/secrets, MCP/Computer Use/browser execution, or Windows input.

## Tests
Cover owner A/B isolation, missing owner, mismatch, owner change during view lifecycle, cross-session contamination, stale identity evidence, four-user executable identity separation, deterministic routing, and immutable source models.

## Evidence / diff
Create `current/AUTOBOT_MISSION_CONTROL_PHASE4K_OWNER_ROUTING.diff` and machine-readable evidence with exact lineage, tests, bounds, owner-isolation result, and authority audit. The diff must not include itself.

## Workflow discipline
Do not manually dispatch workflows. Do not merge automatically. Normal CI remains the verification gate.