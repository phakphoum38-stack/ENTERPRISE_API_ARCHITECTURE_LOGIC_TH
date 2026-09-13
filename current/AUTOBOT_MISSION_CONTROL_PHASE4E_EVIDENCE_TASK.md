# Autobot Mission Control Phase 4E — Evidence Projection Task

## Objective
Implement the next presentation-only Mission Control boundary after Phase 4D UI-schema validation: a deterministic, bounded, owner-scoped projection of existing runtime evidence/provenance.

## Base / lineage
- Target base: current `main` at implementation time.
- Record the exact base SHA in the completion evidence.
- Do not use a failed, unknown, or stale branch as the implementation base.

## Required behavior
- Reuse existing Evidence/Trace/Provenance machinery; do not create a second evidence store.
- Project existing evidence only; never manufacture evidence or upgrade a status.
- Preserve owner isolation and fail closed on owner mismatch.
- Require `read_only=true`.
- Deterministic ordering by stable identifiers/sequence.
- Explicit bounds on records, strings, nesting, and serialized payload size.
- Preserve source/provenance references without exposing secrets or provider response bodies.
- No network calls, execution, mutation, persistence, approval, authorization, policy, skill, registration, MCP, browser, Computer Use, or OS-input authority.
- Reuse `MissionControlUISchemaValidator` from Phase 4D where appropriate.

## Safety rejection
Reject executable descriptors, callbacks, shell/process instructions, dynamic imports, credentials, API keys, bearer tokens, private keys, passwords, arbitrary provider payloads, and mutation instructions.

## Tests
Add focused tests for:
- valid evidence projection
- owner mismatch
- missing/false read_only
- fabricated/unsupported evidence
- secret-like content
- oversized collections/payloads
- nondeterministic ordering
- input immutability
- no execution/mutation authority

## First-class diff
Create `current/AUTOBOT_MISSION_CONTROL_PHASE4E_EVIDENCE.diff` as a clean unified proposal artifact. It must not include itself.

## Evidence
Create machine-readable evidence recording:
- exact base SHA
- exact implementation HEAD SHA
- schema/version
- owner/read-only state
- source authority
- bounds
- tests
- diff artifact
- verification status
- explicit statement that no new execution/authorization/approval/persistence authority was added.

## Workflow discipline
Do not manually dispatch GitHub Actions. Let normal repository automation verify the branch. Do not merge automatically from this task. Merge remains an owner-controlled release decision after authoritative gates pass.

## Completion report
Report branch, exact base/head SHAs, changed files, tests, diff artifact, evidence artifact, CI status, and authority audit.
