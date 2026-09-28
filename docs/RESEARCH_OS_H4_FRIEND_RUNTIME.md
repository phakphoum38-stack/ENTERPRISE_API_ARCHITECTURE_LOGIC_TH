# Research OS H4 — Friend Runtime Boundary

## Purpose

H4 establishes a governed runtime boundary around the existing Owner Special Friend runtime. The runtime remains the execution surface, while this contract binds every exposed operation to the expected Owner identity and exact source SHA.

## Scope

- bind runtime operations to one Owner identity;
- require an exact 40-character source commit SHA for governed execution;
- require a bounded run correlation ID for every governed execution request;
- expose bounded runtime snapshots and agent-run envelopes;
- preserve existing FriendOrchestrator and AgentRuntime ownership;
- keep approval, merge, release, install, workflow dispatch, and authority mutation outside this boundary;
- fail closed on malformed identity, correlation, or runtime output.

## Execution model

```text
Caller
  -> H4 FriendRuntimeContract
      -> owner/source/correlation validation
      -> existing FriendRuntime
          -> FriendOrchestrator / AgentRuntime
      <- bounded execution result
```

H4 does not create a second runtime and does not replace the existing orchestrator. It is a policy boundary around the already-established runtime.

## Identity rules

1. `owner_id` must be non-empty and bounded.
2. `expected_source_sha` must be exactly 40 lowercase hexadecimal characters.
3. The runtime's canonical `source_commit` must exist and equal `expected_source_sha`.
4. `run_correlation_id` must be non-empty and bounded.
5. A mismatch is a hard failure; H4 never guesses or substitutes an identity.

## Allowed operations

- `snapshot()` — bounded read-only runtime state.
- `ask()` — delegate a normal Friend request through the existing orchestrator.
- `run_agent()` — delegate an agent request through the existing AgentRuntime and return a bound envelope.
- `get_agent_run()` — inspect an existing run through the runtime.
- `tool_health()` — expose existing deterministic tool-health information.

## Explicitly outside H4 authority

H4 does not expose or perform:

- approval or denial decisions;
- merge or pull-request mutation;
- release or installation authority;
- workflow dispatch or ref mutation;
- evidence fabrication or rewriting;
- credential handling;
- shell/process/subprocess execution;
- MCP or Computer Use authority.

Existing approval APIs remain owned by the existing approval subsystem and are not promoted into H4 authority.

## Bounds

- owner/correlation text: 2048 characters;
- snapshot serialized payload: 64 KiB;
- run result summary: 2048 characters;
- runtime run list exposed by snapshot: at most 64 entries.

## Failure behavior

Malformed or stale identity, missing source commit, mismatched correlation, unsupported output, oversized output, and dynamic values fail closed with `FriendRuntimeContractError`.

## Evidence and CI

H4 does not manufacture evidence or declare a CI/release gate passed. GitHub Actions remains authoritative for build/test/release evidence. Real commit SHAs are produced by Git; generated artifacts and evidence are produced by the governed workflows.
