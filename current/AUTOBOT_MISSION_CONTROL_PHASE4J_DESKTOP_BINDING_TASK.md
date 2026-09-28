# Autobot Mission Control Phase 4J — Desktop Binding Task

## Objective
Bind the existing Research OS Flutter/Desktop shell to the Phase 4I presentation model without creating a second execution path.

## Required behavior
- Inspect and reuse the existing `owner_special/flutter_app` shell and canonical workspace/chat surfaces.
- Add a Mission Control presentation surface that reads the validated 4H/4I model only.
- Keep the UI responsive and bounded; do not stream unbounded traces, logs, tables, or evidence into the widget tree.
- Preserve explicit states: loading/empty, PASS, FAIL, PENDING, UNKNOWN, truncated, and invalid-source.
- Render provenance/source references as metadata, never as executable links or commands.
- Do not infer success from UI appearance, timestamps, filenames, or missing data.
- Keep owner identity visible and fail closed on owner mismatch.

## Architecture invariant
Flutter is a projection/client layer. `FriendOrchestrator` remains execution authority; `OwnerPolicy` remains authorization authority; `ApprovalGate` remains approval authority. Mission Control must not call those authorities directly to perform actions.

## Explicitly forbidden
No shell/process invocation, PowerShell, command execution, tool execution, MCP calls, browser automation, Computer Use, Windows input, workflow dispatch/retry, build/package/install/uninstall/release/signing, policy mutation, approval mutation, credential handling, or network side effects from widgets or presentation controllers.

## Tests
Add widget/unit tests for valid snapshot rendering, owner mismatch, malformed snapshot, bounded collections, deterministic ordering, all status states, truncation, secret-like payload rejection, no executable callback wiring, and no mutation of the source model.

## Evidence / diff
Create `current/AUTOBOT_MISSION_CONTROL_PHASE4J_DESKTOP_BINDING.diff` plus machine-readable evidence with exact lineage, Flutter files changed, tests, and authority audit. Keep the diff clean and self-exclusion compliant.

## Workflow discipline
Do not manually dispatch workflows and do not merge automatically. Let normal CI verify the branch; merge is owner-controlled.