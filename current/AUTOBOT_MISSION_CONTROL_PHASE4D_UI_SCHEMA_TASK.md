# Autobot Task — Mission Control Phase 4D UI Schema Validation

## Objective
Implement the next logical Mission Control increment as a **read-only, deterministic UI-schema validation boundary**. This is a presentation safety boundary only. Do not create a second execution, authorization, approval, MCP, Computer Use, persistence, or policy authority.

## Exact lineage
Base: `main @ a3f9482aec7cb15aa9073315969882de8e3e67e3`
Task branch: `feat/mission-control-ui-schema-phase4d-autobot-task`

If the branch already contains work, preserve its exact base lineage. Do not rebase onto another branch and do not silently change the base SHA.

## Scope

1. Inspect the existing Mission Control 4A/4B projection and 4C capability projection before adding anything.
2. Reuse existing contracts/helpers where possible; do not duplicate capability health, owner policy, approval, execution, or trace systems.
3. Add a small validator module for UI-neutral Mission Control panel payloads.
4. Define a versioned schema, e.g. `research-os-mission-control-ui/v1`.
5. Permit only explicitly allow-listed presentation structures and scalar/container values.
6. Enforce deterministic ordering where collections are exposed.
7. Enforce bounded payload size and collection lengths.
8. Require `read_only=true` for validated Mission Control payloads.
9. Validate authority declarations and ensure they point to the existing authorities:
   - execution: FriendOrchestrator
   - authorization: OwnerPolicy
   - approval: ApprovalGate
10. Reject executable or dynamic content, including callbacks, code strings intended for execution, dynamic imports, shell/process instructions, event-handler execution descriptors, or arbitrary component constructors.
11. Reject requests/actions that attempt Tool, MCP, browser, Windows input, or Computer Use execution.
12. Reject permission, approval, policy, skill, registration, or provider mutation instructions.
13. Reject credential/secret/token/private-key-like fields and provider response bodies.
14. Preserve owner scope; an owner mismatch must fail closed.
15. Add focused unit/regression tests for valid payloads and malicious/oversized/nondeterministic payloads.
16. Add a clean first-class diff artifact `current/AUTOBOT_MISSION_CONTROL_PHASE4D_UI_SCHEMA.diff` containing only the proposed implementation changes. The diff artifact must not include itself.
17. Add/update documentation describing the validator and explicit non-goals.
18. Produce machine-readable evidence suitable for later verification, but do not execute workflows, merge, or mutate protected gates.

## Required safety properties

- Projection only.
- No execution authority.
- No authorization authority.
- No approval authority.
- No persistence authority.
- No dynamic code execution.
- No network calls.
- No credentials/secrets in output.
- Owner isolation.
- Explicit bounds.
- Deterministic output.
- Fail closed on unknown schema/component/action fields.

## Suggested acceptance tests

- valid read-only Mission Control payload passes
- wrong schema/version fails
- missing read-only flag fails
- unknown panel type fails
- unknown field fails where strict validation is required
- oversized payload fails
- oversized collection fails
- owner mismatch fails
- execution/authorization/approval authority mismatch fails
- callback/function/code payload fails
- dynamic import/process/shell payload fails
- MCP/Computer Use/browser execution descriptor fails
- permission/approval/policy mutation descriptor fails
- credential/token/private-key-like value fails
- ordering is deterministic
- validator does not mutate input

## Workflow rule

Do not manually dispatch GitHub Actions. Push/commit the implementation normally so repository automation can validate it. Do not merge the PR until the authoritative gates pass and the existing owner merge authorization applies.

## Completion contract

At completion, report:
- exact base SHA
- exact HEAD SHA
- files changed
- tests added/passed locally if run
- diff artifact path
- evidence path
- explicit statement that no execution/approval/policy authority was added
- PR number/URL

Then freeze the task branch pending the authoritative gate result.
