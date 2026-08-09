# Research OS AI Brain Core

## Purpose

Research OS Brain Core is the provider-neutral intelligence control plane. AI providers supply model inference; Research OS owns durable context, skills, tools, policy, evidence, memory and execution state.

The Brain does not expose or persist hidden model chain-of-thought. It exposes auditable goals, plans, decisions, evidence, observations and checkpoints instead.

## Phase 1 — Core cognition contract

Implemented:

- Brain identity and Constitution
- goal / intent / constraint / known-unknown model
- durable local-first working memory
- secret-redacted activity ledger
- capability resolution through the existing Agent Registry
- explicit plan contract
- evidence-based verification

## Phase 2 — Context, skills and decisions

Implemented:

- authority-ranked Context Engine
- provenance and conflict preservation
- context budget enforcement
- long-term memory recall port
- versioned Skill Registry
- skill dependency ordering and cycle detection
- skill permission, tool and evidence contracts
- deterministic Decision / Risk Engine
- state-change, network, destructive, secret, release and production risk signals

## Phase 3 — Permissioned tool execution

Implemented:

- Tool Registry contract `brain-tools-phase-3` with explicit metadata and runtime adapters
- capability and permission discovery
- side-effect metadata (`mutating`, `destructive`, `network`, `secret_access`)
- dry-run and idempotency declarations
- Execution Controller as the Brain Runtime execution gate
- explicit permission checks before adapter invocation
- explicit approval for every real mutating tool call
- bounded automatic retry only for idempotent tools
- no automatic retry for non-idempotent tools
- durable execution checkpoints
- interrupted-run recovery marker on restart
- idempotency-key reuse of completed results
- observation records for attempts/results
- activity-ledger events for plan/retry/failure/completion

Initial executable tools are intentionally internal and read-only:

- `brain.skills.inspect`
- `brain.session.inspect`
- `brain.context.inspect`

## Phase 4 — Secret-aware Skill -> Tool execution

Implemented:

- secret redaction contract `brain-secret-redaction-phase-4`
- ephemeral per-execution secret scopes that are never persisted
- automatic discovery of values stored under sensitive input keys
- explicit ephemeral secret values for non-standard credential fields
- value-aware scrubbing of adapter output, exceptions, observations, checkpoints and ledger events
- common Bearer / provider-key shape scrubbing as a second defensive layer
- secret-aware checkpoint and activity-ledger facades while preserving the canonical Activity Ledger
- Tool capability matching contract `brain-tool-matching-phase-4`
- deterministic selection of one ready tool that satisfies all requested capabilities
- Skill Registry contract `brain-skills-phase-4` with `required_tool_capabilities`
- Skill -> Tool execution contract `brain-skill-tool-execution-phase-4`
- skill dependency resolution before execution
- skill-level permission gating before adapter invocation
- tool-level permission / risk / approval gating through the hardened Execution Controller
- post-execution verification against each skill's declared evidence contract
- explicit `verification_failed` instead of treating a successful tool call as a completed skill when evidence is missing
- single-tool skill execution in Phase 4; multi-tool skills are intentionally routed to orchestration rather than guessed

The three internal read-only tools are now sufficient to exercise the Brain execution path and foundational Brain skills. External filesystem, terminal, GitHub, Google Workspace and other adapters are still not automatically trusted or discovered. They must be registered with an explicit ToolDefinition and pass through the same hardened controller.

## Execution contract

```text
Goal
  -> Context
  -> Plan
  -> Skill selection
  -> Skill dependency resolution
  -> Tool capability matching
  -> Decision + Risk
  -> Skill permission check
  -> Tool permission check
  -> Approval gate when mutating
  -> Secret-aware execution scope
  -> Tool adapter
  -> Observation
  -> Checkpoint
  -> Post-execution evidence verification
  -> Memory / Ledger
```

No Brain Runtime method exposes a direct authorization bypass to an adapter. The low-level registry invocation method exists only underneath the governed execution boundary and must not be treated as a public authorization API.

## Retry and recovery

Automatic retries are bounded to at most the configured controller maximum (1-5 attempts) and are enabled only when the ToolDefinition declares the operation idempotent. Non-idempotent tools execute once per explicit execution request.

A process restart converts a checkpoint left in `running` state to `interrupted`. Resuming requires a fresh execution request because persisted checkpoint payloads are redacted and are not a credential-recovery mechanism.

## Secret handling boundary

Phase 4 protects persisted and returned Brain execution records against secrets reflected by adapters under neutral field names or embedded in exception strings. Secret values discovered or supplied for one execution live only in an ephemeral context-local scope and are not included in checkpoints, activity records or diagnostics.

This does not make arbitrary external adapters automatically trusted. Credential-bearing adapters still require explicit registration, least-privilege permissions, provider-specific tests, and production trust-boundary review before promotion.

## Current development boundary

Brain Phase 4 establishes the model-independent control plane and hardened internal execution path. It does not yet add unrestricted filesystem, terminal, GitHub-write, Google Workspace-write or production deployment adapters. Those integrations should arrive as separate permissioned adapter slices with their own evidence and rollback contracts.

## Release boundary

This Brain work is developed on `feature/v2-ai-brain-core`, based on the RC2 AI Gateway hardening branch. It does not modify frozen RC1, merge `main`, create a tag or GitHub Release, publish V2, or deploy V2 production.
