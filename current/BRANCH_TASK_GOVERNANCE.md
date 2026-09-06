# Research OS Branch / Task Governance

Status: CANONICAL
Version: 1

## Purpose

This contract prevents work from contaminating another task's branch, commit lineage, or verification state.

## Core rules

1. One logical task has one working branch.
2. A task branch has exactly one declared base branch and one exact base SHA at creation time.
3. A mutable branch under verification is LOCKED for unrelated work.
4. A failed task becomes QUARANTINED and is not an implicit base for new work.
5. A verified task becomes FROZEN until an explicit follow-up task is created.
6. UNKNOWN branch state or UNKNOWN base SHA must never be used as a new task base.
7. A new task may branch from `main` only when the selected `main` SHA is explicitly recorded as VERIFIED.
8. A stacked task may branch from another task only when that parent task is an explicit dependency and its exact SHA is recorded.
9. Merge decisions require the exact current HEAD SHA, required checks, review/blocker state, lineage, and explicit authorization.
10. Historical branches are evidence, not automatically valid development bases.
11. Branch names do not prove state. State is determined from task metadata and evidence.
12. No workflow is re-run by governance validation; validation is read-only.

## Lifecycle

```text
CREATED -> ACTIVE -> RUNNING -> VERIFIED -> FROZEN -> MERGE_CANDIDATE -> MERGED -> ARCHIVED
                         |
                         +-> QUARANTINED
```

A QUARANTINED branch may be retained for forensic evidence and recovery, but cannot become an implicit base.

## Required task record

Every new task must be representable by these fields:

```yaml
task_id: "256"
purpose: "short deterministic purpose"
repository: "phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH"
branch: "task/256-short-purpose"
base_branch: "main"
base_sha: "<exact 40-char sha>"
parent_task: null
head_sha: "<exact 40-char sha>"
state: ACTIVE
allowed_paths: []
forbidden_paths: []
created_at: "recorded externally; not used as a deterministic source"
```

## State meanings

- `CREATED`: task record exists; no mutation started.
- `ACTIVE`: work is allowed on its isolated branch.
- `RUNNING`: verification/build/analysis is in progress; unrelated work is forbidden on this branch.
- `VERIFIED`: required evidence for the task's declared scope is green.
- `FROZEN`: verified state is retained as an immutable reference for downstream work.
- `MERGE_CANDIDATE`: all merge evidence is present and owner authorization may be requested.
- `MERGED`: GitHub confirms the PR was actually merged.
- `QUARANTINED`: failed, contaminated, ambiguous, or superseded branch retained for evidence; never an implicit base.
- `ARCHIVED`: historical branch retained for traceability; not a development base.

## Naming contract

Preferred active names:

```text
task/<id>-<purpose>
fix/<id>-<purpose>
feat/<id>-<purpose>
security/<id>-<purpose>
release/<version>
quarantine/<id>-<reason>
archive/<purpose>
```

Names such as `tmp`, `tmp2`, `final`, `final2`, `new`, or `clean` do not establish governance state and must not be used for new task branches.

## Protected references

At minimum, these references are treated as protected in the current Friend stack:

- `main`
- `mcp-boundary`
- `computer-use-boundary`

`computer-use-boundary` is currently the active branch for PR #255 and must not receive unrelated work while it is under review.

## Merge gate

```text
Task record
  -> exact base SHA
  -> isolated branch
  -> exact HEAD SHA
  -> required checks
  -> review / blockers
  -> lineage validation
  -> provenance / security evidence
  -> explicit owner authorization
  -> merge
```

The GitHub Merge Status UI is useful evidence for checks, approvals, and blockers, but it does not replace this contract or explicit merge authorization.

## Enforcement principle

A branch name or document alone is not proof of correctness. Governance must be backed by deterministic validation and GitHub evidence. Failed or unknown state must fail closed.
