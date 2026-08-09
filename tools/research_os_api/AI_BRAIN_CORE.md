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

Phase 5 adds adapters that read real project and GitHub state while preserving the Phase 3/4 permission, secret and evidence boundaries. These adapters are opt-in per Brain Tool Registry; they are not globally trusted merely because the code exists.

### Sandboxed workspace pack

Contract: `brain-workspace-read-tools-phase-5`

Implemented tools:

- `workspace.file.read` — bounded UTF-8 text reads
- `workspace.directory.list` — bounded directory browsing
- `workspace.code.search` — bounded source-code text search
- `workspace.repository.map` — bounded relative-path repository map
- `workspace.build.inspect` — static detection of manifests, CI workflows, installer definitions and test files

Workspace safeguards:

- explicit workspace root required at adapter installation time
- absolute paths and `..` traversal rejected
- resolved targets must remain inside the configured workspace
- returned paths are workspace-relative rather than absolute host paths
- common VCS, dependency, build-output and cache directories excluded from broad scans
- common credential directories and credential-file names blocked
- `.env` variants blocked except `.env.example`
- binary / non-UTF-8 content and oversized file reads rejected
- read, search, map and scan counts bounded
- no shell execution and no network access
- every call still requires `workspace.read`

The path denylist is defense in depth, not a claim that every safe-looking source/config file can never contain sensitive text. Phase 4 reflected-secret redaction still applies to adapter results.

### Governed GitHub read pack

Contract: `brain-github-read-tools-phase-5`

Implemented tool:

- `github.repository.dashboard` — compact repository metadata, recent commits, open pull requests and workflow-run status

GitHub safeguards:

- input restricted to `owner/name`; arbitrary URLs are not accepted
- read-only ToolDefinition (`mutating=false`, `destructive=false`)
- network access and possible API-side credential use declared explicitly
- every call requires `github.read`
- no merge, workflow dispatch, commit, release, tag or deployment actions
- adapter output and exceptions stay inside the Phase 4 secret-aware execution boundary
- CI uses an injected deterministic provider instead of live credentials/network calls

## Phase 6 — Approval-gated developer actions

Phase 6 adds narrowly scoped mutation tools without relaxing the Phase 3/4 execution boundary. The adapters remain opt-in and every real mutation is stopped at `awaiting_approval` until an explicit approval is supplied.

### Workspace developer action pack

Contract: `brain-developer-actions-phase-6`

Implemented tools:

- `workspace.file.change` — preview then write/replace one bounded UTF-8 file inside the workspace sandbox
- `workspace.command.run` — run one trusted host-defined test/build/analyze/verify command profile

File-change safeguards:

- dry-run produces a unified diff and an `approval_fingerprint`
- the fingerprint binds `path + action + before_sha256 + after_sha256`
- the fingerprint is an integrity value, not a credential, and is intentionally not named `token`
- actual apply requires both `workspace.read` + `workspace.write`, explicit approval, and the matching fresh fingerprint
- stale workspace state changes the fingerprint and fails closed
- target remains under the Phase 5 workspace/secret-path sandbox
- symlink mutation, binary files, non-UTF-8 files, and oversized files are rejected
- write uses a same-directory temporary file plus atomic `os.replace`
- post-write SHA-256 verification is required
- rollback is a new reverse preview followed by a separate explicit approval; rollback is not silently automatic

Controlled-command safeguards:

- payload selects only a pre-registered `CommandProfile`; payload cannot provide arbitrary shell text or argv
- `shell=False`
- categories are limited to test/build/analyze/verify
- working directory must remain inside the workspace
- command timeout is bounded
- credential-like environment variables are not inherited; only a small runtime environment allowlist is passed
- real execution requires `workspace.execute` plus explicit approval
- Phase 6 does not expose a general terminal/shell adapter

### GitHub write pack

Contract: `brain-github-write-tools-phase-6`

Implemented tools:

- `github.branch.file.upsert` — create or update one UTF-8 file on an explicitly non-protected branch
- `github.pull_request.comment` — add one PR conversation comment without changing code or PR state

GitHub mutation safeguards:

- every real call requires `github.write` and explicit controller approval
- dry-run returns an `approval_fingerprint`; apply requires the same fingerprint
- update requires the expected Git blob SHA; create and update semantics are explicit
- `main`, `master`, `stable`, `production`, `prod` and `release/` / `deploy/` branches are blocked by default
- common secret-bearing repository paths are blocked
- network and credential access are declared explicitly and remain inside the Phase 4 secret-aware boundary
- provider errors do not echo Authorization headers or credentials
- tests inject deterministic mutation providers; CI does not need a live GitHub write credential
- no delete, merge, workflow dispatch, tag, GitHub Release or deployment action exists in this pack

## Skill integration

Phase 5/6 packs participate in the existing Skill -> Tool path. Skills declare required capabilities and permissions; the Tool Registry resolves a matching ready adapter, the controller enforces permissions and approval, and the Brain verifies declared evidence before a skill can be reported as verified.

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
  -> Dry-run / preview when state may change
  -> Approval fingerprint binding
  -> Explicit approval gate
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

This does not make arbitrary external adapters automatically trusted. Credential-bearing adapters still require explicit registration, least-privilege permissions, provider-specific tests and production trust-boundary review before promotion.

## Current development boundary

Brain Phase 6 now has governed workspace edits, trusted-profile test/build execution, non-protected-branch GitHub file upsert and PR comments. It still does **not** expose an unrestricted terminal, arbitrary shell execution, arbitrary filesystem access, file deletion, GitHub merge, workflow dispatch, tag/release creation, Google Workspace writes, installer mutation, release promotion or production deployment.

## Release boundary

This Brain work is developed on `feature/v2-ai-brain-core`, based on the RC2 AI Gateway hardening branch. It does not modify frozen RC1, merge `main`, create a tag or GitHub Release, publish V2, or deploy V2 production.
