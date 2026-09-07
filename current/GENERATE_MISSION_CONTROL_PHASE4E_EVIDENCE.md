# Mission Control Phase 4E — Evidence Projection

Schema: `research-os-mission-control-evidence/v1`

Boundary: presentation-only projection of evidence already present in `AgentRuntime` traces.

## Contract

- reuse existing `AgentRuntime`; no second evidence store;
- owner filtering is applied before projection and mismatch fails closed;
- output is explicitly `read_only=true`;
- records are deterministically ordered by stable `run_id`;
- maximum 100 records, 2048 characters per string, and 64 KiB serialized payload;
- secret-like, executable, shell, callback, and dynamic-import content is rejected;
- only evidence identifiers and lifecycle metadata are projected; provider response bodies and hidden reasoning are not projected;
- no execution, persistence, authorization, approval, registration, network, tool dispatch, MCP, browser, Computer Use, or OS-input authority.

## Existing authority chain

Mission Control remains presentation state only. `FriendOrchestrator` remains execution authority, `OwnerPolicy` authorization authority, `ApprovalGate` approval authority, and `AgentRuntime` the evidence/trace source.
