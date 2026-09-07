# Mission Control Phase 4E — Evidence Projection

Schema: `research-os-mission-control-evidence/v1`

Boundary: presentation-only projection of evidence already present in `AgentRuntime` traces.

## Contract

- source is existing `AgentRuntime`; no second evidence store is created;
- owner filtering is applied before projection;
- output is explicitly `read_only=true`;
- records are deterministically ordered by stable `run_id`;
- record count is bounded to 100 and serialized payload to 64 KiB;
- strings are bounded to 2048 characters;
- secret-like, executable, shell, callback, and dynamic-import content is rejected;
- only evidence identifiers and lifecycle event metadata are projected, not provider response bodies or hidden reasoning;
- projection does not execute, persist, mutate, authorize, approve, register, call tools, use MCP, use browser automation, use Computer Use, or inject OS input.

## Authority

Mission Control remains presentation state only. `FriendOrchestrator`, `OwnerPolicy`, `ApprovalGate`, and `AgentRuntime` retain their existing authorities.
