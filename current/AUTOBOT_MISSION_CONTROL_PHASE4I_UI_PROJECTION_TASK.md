# Autobot Mission Control Phase 4I — UI Projection Adapter Task

## Objective
Implement the first desktop-facing adapter after the unified read-only snapshot: convert the validated Mission Control snapshot into a stable presentation model for the existing Research OS Flutter/Desktop shell.

## Required behavior
- Consume only the Phase 4H unified snapshot; do not call tools, MCP, Computer Use, workflows, providers, or OS input from the presentation adapter.
- Reuse `MissionControlUISchemaValidator`; do not create a second schema authority.
- Preserve `owner_id`, `read_only=true`, exact authority declarations, source/provenance references, and deterministic ordering.
- Permit only the existing presentation panel types: `text`, `metric`, `status`, `table`, `timeline`, `capability-health`.
- Convert source data to immutable UI-safe view models; no callbacks, executable descriptors, commands, dynamic constructors, imports, or arbitrary widgets.
- Apply explicit bounds to panels, rows, steps, strings, nesting, and serialized payload size.
- Fail closed on malformed, conflicting, owner-mismatched, stale, secret-like, or executable content.
- Preserve PASS/FAIL/PENDING/UNKNOWN without reinterpretation or implicit approval.

## UI boundary
The adapter is presentation-only. Flutter widgets may render the resulting view model but must not gain execution, authorization, approval, policy, persistence, network, tool, MCP, browser, Computer Use, Windows-input, build, install, or release authority.

## Tests
Cover valid projection, owner isolation, read-only enforcement, deterministic ordering, all panel types, bounds/truncation, malformed source data, conflicting source values, executable/dynamic content, secrets/credentials, input immutability, and repeated identical input producing identical output.

## Evidence / diff
Create `current/AUTOBOT_MISSION_CONTROL_PHASE4I_UI_PROJECTION.diff` and machine-readable evidence containing exact base/head SHAs, schema versions, source snapshot, bounds, tests, verification state, and authority audit. The diff must not include itself.

## Workflow discipline
Do not manually dispatch GitHub Actions. Do not merge automatically. Normal CI is verification; merge remains owner-controlled after authoritative gates pass.

## Completion report
Report exact lineage, changed files, tests, diff artifact, evidence artifact, CI state, and confirmation that no new authority was introduced.