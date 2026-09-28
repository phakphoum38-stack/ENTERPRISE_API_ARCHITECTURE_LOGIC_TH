# Autobot Mission Control Phase 5E — Read-Only Refresh and Snapshot Synchronization Task

## Objective
Add a safe, deterministic refresh/synchronization boundary for the Mission Control desktop surface without introducing a second runtime, polling authority, or hidden side-effect path.

## Base / lineage
- Continue from the exact current Mission Control development branch HEAD.
- Preserve exact base SHA and HEAD SHA in the completion evidence.
- Do not silently rebase onto a moving branch.

## Scope
Implement a desktop-facing read-only synchronization layer that consumes the canonical Mission Control unified snapshot from Phase 4H and the validated presentation path from Phase 4I/Phase 5A–5D.

The synchronization layer may:
- request a fresh snapshot from an already-existing read-only source contract;
- replace the current immutable snapshot only after validation succeeds;
- expose explicit synchronization state and timestamps/sequence metadata supplied by the source;
- preserve owner/session identity, `read_only`, authority declarations, provenance, truncation, and uncertainty;
- coalesce redundant refresh requests while preserving deterministic ordering;
- reject stale, conflicting, malformed, oversized, owner-mismatched, or schema-invalid snapshots.

The synchronization layer must not:
- execute FriendOrchestrator work;
- invoke tools, MCP calls, browser actions, Computer Use, shell/process commands, Windows input, or network side effects;
- create a new execution/authorization/approval authority;
- infer PASS/FAIL/PENDING/UNKNOWN from timing, absence, filenames, or UI state;
- mutate OwnerPolicy, ApprovalGate, SkillRegistry, provider configuration, registrations, credentials, or release state;
- silently retry failed execution;
- perform background polling unless the existing read-only source contract explicitly permits bounded polling;
- cache data across owner/session boundaries;
- retain mutable references to source payloads.

## Synchronization contract
Define an explicit versioned contract for refresh results, for example:
- schema identifier and version;
- owner/session identity;
- source identity;
- snapshot sequence/version when supplied by the source;
- synchronization state;
- `read_only=true`;
- validated snapshot payload;
- truncation/uncertainty metadata;
- source timestamp only when authoritative source metadata supplies it.

Required synchronization states should distinguish at least:
- `IDLE`
- `REQUESTING`
- `UPDATED`
- `UNCHANGED`
- `STALE_REJECTED`
- `INVALID_REJECTED`
- `OWNER_MISMATCH_REJECTED`
- `SOURCE_UNAVAILABLE`
- `UNKNOWN`

Do not invent freshness semantics that the source cannot prove. If source sequencing is unavailable, fail closed rather than pretending a newer snapshot exists.

## Validation and determinism
- Reuse the Phase 4D UI schema validator and Phase 4H unified snapshot contract.
- Validate before publication to the desktop projection.
- Treat snapshots as immutable after acceptance.
- Keep deterministic field ordering and stable collection ordering.
- Bound every refresh payload and collection using canonical limits.
- Reject executable/dynamic descriptors, callbacks, arbitrary constructors, code strings, shell/process instructions, credentials, secrets, tokens, private keys, provider response bodies, and mutation descriptors.
- Reject owner/session mismatch before publication.
- Never downgrade a known authoritative status merely because a refresh is pending.

## Flutter integration
Wire the synchronization boundary into the existing Mission Control desktop surface without creating a second shell authority.

The UI must render:
- current synchronization state;
- last accepted snapshot metadata;
- explicit stale/invalid/source-unavailable conditions;
- unchanged vs updated state without visual ambiguity;
- bounded progress/diagnostic information.

A refresh control, if present, is presentation-only: it may request the approved read-only synchronization operation, but it must never contain direct runtime execution logic or hidden side effects.

## Tests / evidence
Add focused unit/widget/integration coverage for:
1. valid read-only refresh;
2. unchanged snapshot deduplication;
3. newer sequence accepted;
4. stale sequence rejected;
5. malformed snapshot rejected;
6. owner mismatch rejected;
7. oversized payload rejected;
8. conflicting source metadata rejected;
9. source unavailable/unknown handling;
10. deterministic repeated refreshes;
11. immutable accepted snapshots;
12. owner/session cache isolation;
13. no execution/tool/MCP/Computer Use side effects;
14. UI correctly renders synchronization states without changing authority.

Produce:
- clean `current/AUTOBOT_MISSION_CONTROL_PHASE5E_READONLY_REFRESH_SYNC.diff` containing only the intended changes;
- machine-readable evidence with exact base/head SHA, schema/version, bounds, test paths/results, diff hash, synchronization states, and authority declarations;
- documentation describing the synchronization boundary and its failure semantics.

## Authority invariants
Exactly one authority remains for each concern:
- execution → `FriendOrchestrator`
- authorization → `OwnerPolicy`
- approval → `ApprovalGate`
- trace source → `AgentRuntime`
- presentation → Mission Control UI only
- synchronization → read-only adapter only; it may not become an execution authority.

## Workflow discipline
- Do not manually dispatch GitHub Actions.
- Do not merge the PR.
- Do not mutate protected release gates.
- Do not weaken existing gates to make tests pass.

## Completion report
Report:
- exact base SHA;
- exact implementation HEAD SHA;
- changed files;
- tests and results;
- diff artifact path and SHA-256;
- machine-readable evidence path;
- synchronization contract/schema version;
- explicit confirmation that no new execution, authorization, approval, policy, tool, MCP, Computer Use, or release authority was introduced;
- PR URL.
