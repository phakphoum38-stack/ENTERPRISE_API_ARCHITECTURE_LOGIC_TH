# P1-02 Friend Runtime Correlation Binding

Status: experimental, branch-only.

The existing Friend Runtime Contract already required an external run correlation
ID at its boundary. This slice now carries that same value into the existing
AgentRun lifecycle instead of leaving it only in the response envelope.

Flow:

FriendRuntimeContract.run_agent(run_correlation_id)
→ FriendRuntime.run_agent(...)
→ AgentRuntime.run(..., run_correlation_id=...)
→ AgentRun.run_correlation_id + run-created trace event

No new runtime, queue, scheduler, worker, state machine, or evidence engine is
introduced. The existing AgentRun remains the runtime lifecycle authority.
