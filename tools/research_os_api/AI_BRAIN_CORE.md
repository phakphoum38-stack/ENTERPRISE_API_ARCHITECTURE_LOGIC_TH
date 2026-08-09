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
- key-based redaction for persisted tool payload/evidence/output fields

Initial executable tools are intentionally internal and read-only:

- `brain.skills.inspect`
- `brain.session.inspect`
- `brain.context.inspect`

External filesystem, terminal, GitHub, Google Workspace and other adapters are not automatically trusted or discovered. They must be registered with an explicit ToolDefinition and routed through the same Execution Controller before use.

## Execution contract

```text
Goal
  -> Context
  -> Plan
  -> Skill / Capability selection
  -> Tool selection
  -> Decision + Risk
  -> Permission check
  -> Approval gate when mutating
  -> Tool adapter
  -> Observation
  -> Checkpoint
  -> Verification / Evidence
  -> Memory / Ledger
```

No Brain Runtime method exposes a direct adapter invocation path. The low-level registry invocation method exists for the Execution Controller boundary and must not be treated as an authorization API.

## Retry and recovery

Automatic retries are bounded to at most the configured controller maximum (1-5 attempts) and are enabled only when the ToolDefinition declares the operation idempotent. Non-idempotent tools execute once per explicit execution request.

A process restart converts a checkpoint left in `running` state to `interrupted`. Resuming requires a fresh ExecutionRequest because persisted checkpoint payloads are redacted and are not a secret-recovery mechanism.

## Current hardening boundary

The current persistence redactor is key-based. Tool adapters that handle secret material must declare `secret_access`, must not intentionally return raw secret values, and require an additional secret-aware output hardening slice before external credential-bearing adapters are promoted to production use.

## Release boundary

This Brain work is developed on `feature/v2-ai-brain-core`, based on the RC2 AI Gateway hardening branch. It does not modify frozen RC1, merge `main`, create a tag or GitHub Release, publish V2, or deploy V2 production.
