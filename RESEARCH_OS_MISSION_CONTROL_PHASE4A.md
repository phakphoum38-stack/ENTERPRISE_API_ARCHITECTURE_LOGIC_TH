# Research OS — Mission Control Phase 4A

## Purpose

Add a deterministic, read-only Mission Control projection over the existing
`AgentRuntime` trace model. This is the first presentation-layer contract for
an agent-native workspace and does not create a second execution authority.

## Lifecycle view

Mission Control exposes the observable chain:

`goal -> plan -> tool/action -> result -> evidence -> decision`

The current AgentRuntime trace provides the high-level lifecycle events that
are safe to expose:

- `run-created`
- `planning`
- `executing`
- `verifying`
- `completed` or `failed`

## Authority boundaries

- `FriendOrchestrator` remains execution authority.
- `OwnerPolicy` remains authorization authority.
- `ApprovalGate` remains approval authority.
- `AgentRuntime` remains trace/lifecycle authority.
- `MissionControl` is presentation/projection only.

Mission Control must never execute a tool, authorize a tool, mutate a skill,
change policy, or grant approval.

## Owner isolation

Snapshots are owner-scoped through `AgentRuntime.list_runs(owner_id=...)`.
Individual run lookup additionally verifies that the recovered run belongs to
the requested owner. A run from another owner is therefore not projected.

## Bounded projection

- Maximum snapshot runs: 100.
- Default snapshot limit: 25.
- Maximum events projected per run: 250.
- The projection reports when events were truncated.

The limits prevent an unbounded trace store from becoming an unbounded UI
payload.

## Evidence and privacy

Mission Control projects evidence identifiers and high-level provider/tool
metadata already present in the trace. It does not persist or reconstruct
model hidden reasoning, credentials, or full provider response bodies.

## API contract

`MissionControl.snapshot()` returns:

- schema/version
- owner identity
- read-only flag
- authority declarations
- ordered recent runs
- per-run lifecycle events
- evidence id/provider when available
- status counts

`MissionControl.run(run_id)` returns one owner-validated run projection or
`None` when it cannot be safely projected.

## Explicit non-goals

This phase does not add:

- browser automation
- Windows input automation
- tool execution
- new permissions
- MCP execution
- provider response persistence
- dynamic UI code execution
- automatic promotion or release behavior

## Next increments

1. Connect this projection to the desktop shell as a read-only timeline.
2. Add structured step categories for goal/plan/tool/result/evidence/decision.
3. Add capability and tool-health panels using existing read-only catalog data.
4. Add safe UI-schema validation before dynamic panels are rendered.
5. Keep every action behind the existing orchestrator/policy/approval gates.
