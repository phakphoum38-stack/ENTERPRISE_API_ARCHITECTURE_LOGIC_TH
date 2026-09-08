# Canonical History — #111 → #115 → #116 → FINAL → LOCK

**Status:** CANONICAL HISTORICAL RECORD

**Repository:** `phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH`

**History cutoff:** 2026-09-08 / 2026-09-09 verification session

**Purpose:** Preserve the verified engineering history of the Evidence Hub / canonical evidence release spine so that future refactors, repairs, or cleanup cannot erase the reason a change existed, the exact SHA lineage, or the evidence that exposed a defect.

> This document is append-oriented. Historical evidence must not be rewritten to make an old run appear healthy. Corrections belong in a new entry that references the original evidence.

## 1. Canonical release spine

The intended chain is:

`#111 → canonical evidence → #115 → #116 → FINAL → LOCK`

The evidence workflow is the driver for the canonical lineage boundary. It must reconcile the actual main target, bind evidence to the exact PR/head/merge lineage, and fail closed when lineage cannot be proven.

No production-health implementation is duplicated merely to satisfy the evidence chain.

## 2. First verified lineage repair — PR #313

### PR

- **PR:** #313
- **Title:** `fix(ci): bind evidence lineage to current main target`
- **State:** merged
- **Base SHA:** `58b5b54d6f5c733dec73a02e9138afbc5a8f775f`
- **PR head SHA:** `7302c90db92552963a2e4b2d476fc859df4122af`
- **Merge SHA:** `a988ef4b7a4b1c0f539c0ee121cca8183f1938cd`
- **Merged at:** `2026-09-08T19:12:55Z`
- **Changed file:** `.github/workflows/research-os-evidence-lineage.yml`

### Root cause fixed by #313

The existing #111 evidence workflow's `workflow_dispatch` inputs contained historical hard-coded defaults. The `push: main` path could therefore reconcile stale historical PR/base/head/merge values instead of the commit that actually reached `main`.

#313 changed the push path to:

1. use the actual `github.sha` as the merge target;
2. resolve the uniquely associated merged PR from the merge commit through the GitHub API;
3. derive the current PR base/head/merge SHAs from GitHub PR metadata;
4. fail closed if exactly one merged PR cannot be resolved;
5. bind generated evidence/artifacts to the resolved current head SHA;
6. retain the squash-lineage proof model where the PR head is not a direct parent.

This was an evidence-driver contract correction, not a production implementation change.

## 3. #313 canonical main run

### Workflow run

- **Workflow:** `Research OS Evidence Lineage`
- **Run ID:** `34267645440`
- **Run number:** `104`
- **Event:** `push`
- **Branch:** `main`
- **Head SHA:** `a988ef4b7a4b1c0f539c0ee121cca8183f1938cd`
- **Run started:** `2026-09-08T19:12:58Z`
- **Completed:** `success`
- **Created:** `2026-09-08T19:12:58Z`
- **Updated:** `2026-09-08T19:13:15Z`

The workflow completed successfully and produced the canonical evidence artifact.

## 4. Historical defect discovered after #313

The #313 artifact contained:

```json
"generated_by": "research-os-evidence-lineage",
"generated_at": ""
```

The run metadata simultaneously proved:

```text
Actions run 34267645440
run_started_at = 2026-09-08T19:12:58Z
```

The workflow log also showed the runtime value `RUN_STARTED_AT` as empty.

### Root cause

The #313 workflow used:

```yaml
RUN_STARTED_AT: ${{ github.run_started_at }}
```

`run_started_at` is not a valid property of the GitHub Actions `github` context. The expression therefore resolved to an empty string. The Python producer then correctly serialized that empty environment value into `generated_at`.

Therefore the defect was **not** in the lineage algorithm or JSON writer. It was a provenance-source contract error at the GitHub Actions context boundary.

### Historical evidence rule

The empty `generated_at` in the #313 artifact is retained as **historical evidence of the defect**.

It must not be edited, regenerated, or overwritten merely to make history appear correct.

## 5. Root fix — PR #314

### PR

- **PR:** #314
- **Title:** `fix(evidence): source generated_at from Actions run metadata`
- **State:** merged
- **Base:** `main`
- **Base SHA:** `a988ef4b7a4b1c0f539c0ee121cca8183f1938cd`
- **Head branch:** `fix/canonical-evidence-run-started-at`
- **Head SHA:** `d85bac4b509d7bab86b4d3f8f4f770301a54ed52`
- **Merge SHA:** `57cebb1ed7c0e54293ee3198cd37e8569c955762`
- **Merged at:** `2026-09-08T20:07:53Z`
- **Changed files:** 1
- **Additions/deletions:** `+8 / -2`

### Exact fix

The job-level invalid context variable is removed.

The producer now obtains `GITHUB_RUN_ID`, calls the Actions Run REST API for the current run, reads `run_started_at`, and fails closed if that value is missing.

The evidence producer now writes:

```python
"generated_at": run_started_at
```

instead of reading the invalid environment variable.

### Required invariant

For every canonical evidence production run:

```text
Actions API actions/runs/{GITHUB_RUN_ID}.run_started_at
==
canonical-evidence.json.generated_at
```

A missing or empty timestamp is a producer failure, not a valid artifact state.

## 6. #314 CI verification at history cutoff

The #314 head SHA had successful pull-request checks including:

- `Generate Orchestrator` — success
- `Assistant Mesh 30 Gate` — success
- `Research OS CI Lite` — success
- `V3.5 Master Final Gate` — success
- `Research OS Unified 10x10 Exact SHA Gate` — success
- `Research OS Final Gate` — success
- `Research OS Gate` — success

Notably, the `Research OS Evidence Lineage` workflow is a `push: main` producer. Therefore PR #314 checks alone do **not** prove the post-fix canonical artifact timestamp invariant. The decisive verification is the first main push after #314 is merged.

## 7. Mandatory post-merge verification

After #314 reaches `main`, verify the newly generated canonical evidence in this order:

1. identify the new `Research OS Evidence Lineage` run;
2. record its run ID, head SHA, status, conclusion, and `run_started_at` from the Actions API;
3. inspect the canonical evidence artifact;
4. read `canonical-evidence.json.generated_at`;
5. compare it byte-for-byte as the timestamp string against Actions API `run_started_at`;
6. verify the evidence head/merge/base lineage still matches the actual merged PR;
7. retain both the old #313 artifact and the new corrected artifact;
8. only then treat the timestamp contract as repaired.

The expected proof is:

```text
OLD #313:
run_started_at = 2026-09-08T19:12:58Z
generated_at   = ""
STATUS         = historical defect evidence

NEW post-#314 run:
run_started_at = <new Actions API timestamp>
generated_at   = <same exact timestamp>
STATUS         = corrected canonical evidence
```

## 8. What must never be done

- Do not rewrite the #313 artifact to insert a timestamp.
- Do not delete the failed/defective evidence that explains why #314 exists.
- Do not replace an Actions API timestamp with the step's local `date -u` value when the contract is specifically workflow run start time.
- Do not silently reintroduce hard-coded PR/base/head/merge defaults.
- Do not mark a lineage stage GREEN from file presence alone.
- Do not claim #314 repaired the canonical artifact until a post-merge main run proves the invariant.
- Do not create a parallel evidence producer when the canonical #111 driver already owns the boundary.
- Do not change historical SHAs to current SHAs in old records.

## 9. Evidence hierarchy

When reconstructing this history, use the following authority order:

1. GitHub commit/PR metadata and immutable SHA lineage.
2. GitHub Actions Run REST API metadata.
3. Workflow job/check results and logs.
4. Uploaded canonical artifacts.
5. Repository documentation and derived summaries.
6. Human commentary.

When prose conflicts with executable evidence or GitHub metadata, the immutable GitHub/Actions evidence wins and the discrepancy must be recorded.

## 10. Canonical SHA chain currently proven

```text
#313 base
58b5b54d6f5c733dec73a02e9138afbc5a8f775f
        |
        | PR #313 head
        v
7302c90db92552963a2e4b2d476fc859df4122af
        |
        | squash merge
        v
a988ef4b7a4b1c0f539c0ee121cca8183f1938cd
        |
        | PR #314 base
        v
d85bac4b509d7bab86b4d3f8f4f770301a54ed52
        |
        | pending merge / post-merge verification
        v
#115 → #116 → FINAL → LOCK
```

## 11. Status at history cutoff

| Area | Status | Evidence |
|---|---|---|
| #313 stale-main-target defect | FIXED / MERGED | PR #313 |
| #313 canonical lineage run | GREEN | run `34267645440` |
| #313 `generated_at` | DEFECTIVE / HISTORICAL | artifact from run `34267645440` |
| Root cause of empty timestamp | PROVEN | invalid `github.run_started_at` context property |
| #314 root fix | IMPLEMENTED | commit `d85bac4b509d7bab86b4d3f8f4f770301a54ed52` |
| #314 PR checks | GREEN | seven recorded successful workflow runs |
| #314 merged to main | NOT YET PROVEN AT CUTOFF | PR still open |
| Post-fix canonical artifact | PENDING | must be verified on main push |
| #115 readiness | BLOCKED ON CANONICAL EVIDENCE CONFIRMATION | release spine contract |
| #116 / FINAL / LOCK | NOT TO BE ADVANCED FROM UNVERIFIED TIMESTAMP | preserve gate order |

## 12. Change-control rule for future maintainers

This file is a historical ledger, not a scratchpad.

If a future change modifies the evidence producer, lineage contract, timestamp source, release spine, or gate semantics:

- append a new dated section;
- record the exact PR and commit SHAs;
- record the old invariant and new invariant;
- identify the root cause or design reason;
- preserve references to the superseded evidence;
- record the validating workflow run IDs and artifacts;
- never silently rewrite the historical narrative.

The canonical objective is reproducibility: another engineer must be able to reconstruct **what happened, why it happened, what was changed, what evidence proved it, and what remains unproven** without relying on memory or chat history.

## 13. Post-#316 verification — corrected canonical evidence and production gate

**Verification date:** 2026-09-08 / 2026-09-09 session

PR #314 was subsequently merged as proven by GitHub metadata:

- **PR #314 merge SHA:** `57cebb1ed7c0e54293ee3198cd37e8569c955762`
- **Merged at:** `2026-09-08T20:07:53Z`

PR #316 then wired the existing production-readiness capabilities into the V3.5 Master Final Gate without introducing a parallel production implementation.

- **PR:** #316
- **Title:** `feat(115): wire production readiness evidence into final gate`
- **Merged main SHA:** `565ab068d5a1540ea799b594ff031ba003e068af`
- **Final Gate candidate SHA:** `443bf21d88bebe30c4359b24cb0e9d34e9a22189`

### Post-#316 canonical evidence — main

The `Research OS Evidence Lineage` push workflow executed on `main` at run `34277345868` and completed successfully against main SHA `565ab068d5a1540ea799b594ff031ba003e068af`.

The produced artifact was:

- **Artifact:** `canonical-evidence-lineage-443bf21d88bebe30c4359b24cb0e9d34e9a22189`
- **Artifact digest:** `sha256:1744c9178af0bfe8d8e87a12409d26e5f9a44abc4b4f0201fbd14a92718ec3fc`
- **Artifact expiry:** `2026-12-07T20:52:43Z`

The canonical evidence content proves:

```text
status                 = GREEN
stage                  = #111
base_sha               = 57cebb1ed7c0e54293ee3198cd37e8569c955762
pr_number              = 316
head_sha               = 443bf21d88bebe30c4359b24cb0e9d34e9a22189
merge_sha              = 565ab068d5a1540ea799b594ff031ba003e068af
head_matches_pr       = true
merge_matches_pr      = true
head_is_merge_parent  = true
base_matches_parent   = true
direct_parent_lineage  = true
pr_merged              = true
traceability_gap       = null
next_stage              = #115
```

Most importantly, the corrected producer wrote:

```text
generated_at = 2026-09-08T20:52:43Z
```

which matches the Actions run `34277345868.run_started_at = 2026-09-08T20:52:43Z` exactly. This closes the historical #313 timestamp defect without rewriting the defective #313 artifact.

### Production readiness gate — existing capabilities reused

`V3.5 Master Final Gate` run `34276318465` completed successfully on candidate SHA `443bf21d88bebe30c4359b24cb0e9d34e9a22189`.

Production readiness job `102230098982` passed all of its stages:

- validate production readiness assets;
- execute the existing backup/restore recovery drill;
- execute existing worker recovery and observability evidence;
- publish production readiness evidence;
- upload production readiness evidence.

The production-readiness artifact was:

- **Artifact ID:** `10075848376`
- **Digest:** `sha256:dfe060a38732bf8d4a4349d8e7fdb3018fdcc42bebe1c5ae8aeee3608f783ea9`
- **Schema:** `research-os.production-readiness.v1`
- **Status:** `PASS`
- **Production mutation:** `false`

Evidence classes recorded by that gate:

```text
deployment-config: render.yaml + /health + autoDeploy
staging-boundary: render.staging.yaml
backup-restore: executable isolated recovery drill
worker-recovery-observability: existing governed test surfaces
```

The first backup-drill failure was traced to the gate incorrectly checking `$LASTEXITCODE` after invoking a PowerShell script. The subsequent test failure was traced to Windows SQLite cleanup during temporary-directory removal, while the recovery semantics themselves were already proven. The final candidate gate run passed after the cleanup fix; no duplicate backup/restore or worker-recovery implementation was introduced.

### Main verification set

For merged main SHA `565ab068d5a1540ea799b594ff031ba003e068af`, the post-merge push evidence includes successful runs for:

- `Research OS Evidence Lineage` — `34277345868` — success
- `Assistant Mesh 30 Gate` — `34277345890` — success
- `Research OS Unified 10x10 Exact SHA Gate` — `34277346029` — success
- `Research OS Gate` — `34277345936` — success
- `Continuous Generated Release` — `34277345865` — success
- `Research OS Windows Artifact` — `34277362322` — success
- `Workflow Intelligence` — `34277676535` — success

`Workflow Intelligence` run `34277676535` also recorded the merged main SHA as its head SHA and completed successfully.

### Release-spine status after #316

```text
#111
  ↓
Canonical Evidence — GREEN / traceability_gap = null
  ↓
#115
  ↓
Existing Compatible Production Readiness Tools — PASS
  ↓
#116
  ↓
FINAL
  ↓
LOCK
```

The historical sections above remain unchanged in meaning and are preserved intentionally. This section is the append-only post-#316 correction and verification record.

## 14. Current handoff rule

The canonical evidence producer is now proven against the merged main target, and the production-readiness gate is proven on the exact candidate that became main. Future release work must continue from `565ab068d5a1540ea799b594ff031ba003e068af` and must not reopen the historical #313 defect as if it were current.

If a future gate fails, preserve the exact failing run and root cause, repair only the responsible governed surface, and re-run the affected gate. Do not manufacture GREEN from historical or unrelated runs.
