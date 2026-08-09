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

## Phase 5 — Real read-only developer adapters

Phase 5 adds the first adapters that read real project and GitHub state while preserving the Phase 3/4 permission, secret and evidence boundaries. These adapters are opt-in per Brain Tool Registry; they are not globally trusted merely because the code exists.

### Sandboxed workspace pack

Contract: `brain-workspace-read-tools-phase-5`

Implemented tools:

- `workspace.file.read` — bounded UTF-8 text reads
- `workspace.directory.list` — bounded directory browsing
- `workspace.code.search` — bounded source-code text search
- `workspace.repository.map` — bounded relative-path repository map
- `workspace.build.inspect` — static detection of manifests, CI workflows, installer definitions and test files

Workspace safeguards:

- an explicit workspace root is required at adapter installation time
- absolute paths and `..` traversal are rejected
- resolved targets must remain inside the configured workspace
- returned paths are workspace-relative rather than absolute host paths
- common VCS, dependency, build-output and cache directories are excluded from broad scans
- common credential directories and credential-file names are blocked
- `.env` variants are blocked except `.env.example`
- binary / non-UTF-8 content and oversized file reads are rejected
- read, search, map and scan counts are bounded
- adapters do not execute shell commands
- adapters do not use the network
- every call still requires `workspace.read` through the existing Execution Controller

The path denylist is a defense-in-depth boundary, not a claim that every safe-looking source/config file can never contain sensitive text. Phase 4 reflected-secret redaction still applies to adapter results, and additional domain-specific secret rules can be added as adapters expand.

### Governed GitHub read pack

Contract: `brain-github-read-tools-phase-5`

Implemented tool:

- `github.repository.dashboard` — compact repository metadata, recent commits, open pull requests and workflow-run status using the existing read-only GitHub dashboard provider

GitHub safeguards:

- input is restricted to `owner/name`; arbitrary URLs are not accepted by the Phase 5 adapter
- the ToolDefinition is read-only (`mutating=false`, `destructive=false`)
- network access and possible API-side credential use are declared explicitly (`network=true`, `secret_access=true`)
- every call requires `github.read`
- no merge, workflow dispatch, commit, release, tag or deployment actions are exposed
- adapter output and exceptions remain inside the Phase 4 secret-aware execution boundary
- CI uses an injected deterministic provider rather than live GitHub credentials/network calls

### Skill integration

Both Phase 5 packs participate in the existing Skill -> Tool path. A skill may declare a required capability such as `workspace_file_read` or `github_repository_read`; the Tool Registry resolves a ready matching adapter, the controller enforces permissions, and the Brain verifies required evidence after execution before reporting the skill as verified.

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

Brain Phase 5 now has governed read-only workspace and GitHub status adapters. It still does not add unrestricted filesystem access, terminal execution, filesystem write, GitHub write, Google Workspace write or production deployment adapters. Those integrations must arrive as separate permissioned slices with explicit mutation metadata, approval, evidence, recovery and rollback contracts.

## Release boundary

This Brain work is developed on `feature/v2-ai-brain-core`, based on the RC2 AI Gateway hardening branch. It does not modify frozen RC1, merge `main`, create a tag or GitHub Release, publish V2, or deploy V2 production.
