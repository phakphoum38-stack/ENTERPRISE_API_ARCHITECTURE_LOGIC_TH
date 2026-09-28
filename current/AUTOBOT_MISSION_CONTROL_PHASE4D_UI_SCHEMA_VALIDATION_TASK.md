# Autobot Task — Mission Control Phase 4D UI Schema Validation

Add a bounded, deterministic, read-only UI-schema validation boundary for Mission Control dynamic panels.

Base target: `main @ a3f9482aec7cb15aa9073315969882de8e3e67e3`.

Validation only. Do not execute UI actions, tools, MCP, browser automation, Windows input, or provider calls. Reuse existing validators/contracts where possible; do not duplicate an existing schema authority.

Validate schema/version, allow-listed panel identity/type, bounded fields/collections, primitive JSON-compatible values, deterministic ordering, explicit read-only semantics, authority declarations, and owner scope where present.

Reject executable code/callbacks, arbitrary widgets/components, dynamic imports, tool/MCP invocation instructions, browser/Computer Use actions, permission/approval mutations, credential-like values, unbounded payloads, unknown schema versions, and owner mismatches.

Return structured validation results without mutating the source projection. Add regression tests for valid/malformed/oversized/executable/unknown-schema/owner-mismatch inputs. Add a clean first-class `.diff` artifact that excludes itself. Update Mission Control docs with Phase 4D contract and non-goals.

Safety invariants: FriendOrchestrator remains execution authority; OwnerPolicy authorization authority; ApprovalGate approval authority; AgentRuntime trace authority; Mission Control remains presentation/projection only; existing catalog/health/runtime authorities remain unchanged; no new permissions; no workflow execution requested.

Before PR: compile, focused tests, full owner_special tests, clean self-excluding diff validation, exact base/head SHA evidence. Do not manually dispatch workflows. Merge only after exact HEAD passes authoritative gates and lineage/provenance/review gates; existing owner authorization to merge passing work applies.

Out of scope: dynamic UI execution, Flutter renderer implementation, browser automation, Computer Use execution, MCP execution, tool registration, policy/approval changes, self-learning promotion, release workflow changes.
