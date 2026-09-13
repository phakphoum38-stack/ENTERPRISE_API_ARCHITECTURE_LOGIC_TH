# Research OS Mission Control — Phase 4D UI Schema Boundary

## Contract
`MissionControlUISchemaValidator` validates a UI-neutral Mission Control payload before presentation.

Schema: `research-os-mission-control-ui/v1`

The boundary is strict, bounded, owner-scoped, deterministic, and read-only.

## Allowed projection
- root metadata and the three existing authority declarations
- bounded `panels`
- allow-listed panel types: `text`, `metric`, `status`, `table`, `timeline`, `capability-health`
- scalar presentation values and bounded lists/maps

## Required safety
- `read_only` must be exactly `true`
- owner mismatch fails closed
- authority declarations must remain `FriendOrchestrator`, `OwnerPolicy`, and `ApprovalGate`
- panel IDs must be deterministically ordered
- payload bytes, nesting, strings, panels, and collections are bounded
- unknown root/panel fields and panel types fail closed
- callbacks, executable code, dynamic imports, shell/process instructions, MCP/Computer Use/browser execution descriptors, mutation instructions, and credential-like values are rejected
- unsupported dynamic Python objects are rejected
- validation does not mutate the input

## Non-goals
This module does not execute tools, MCP, browser, Windows input, Computer Use, callbacks, or code. It does not authorize actions, grant approvals, mutate policy/skills/registration/provider state, persist runtime state, or make network calls.

## Authority model
- Execution authority: `FriendOrchestrator`
- Authorization authority: `OwnerPolicy`
- Approval authority: `ApprovalGate`
- Presentation validation authority: this bounded validator only

The validator is a safety boundary, not a new execution or authorization authority.
