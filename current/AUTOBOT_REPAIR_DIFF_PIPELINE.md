# Autobot Repair Diff Pipeline

## Purpose

Workflow Intelligence may diagnose a failure and propose a repair, but a repair is not trusted merely because it was generated. The canonical intermediate artifact is a unified `repair.diff` that can be inspected, hashed, validated, and only then explicitly applied.

## Lifecycle

`Failure → Analysis → Repair Plan → Generate repair.diff → Validate → Review → Apply on task branch → Verify → Evidence → Continue`

## Boundaries

- Diff generation is proposal-only and does not mutate the working tree.
- Validation is deterministic and path-bounded.
- Protected release/provenance workflow files cannot be auto-repaired.
- Applying a diff is explicit and never targets `main` automatically.
- Generated proposals must be saved and reviewed before `--apply` can be used.
- Evidence is a first-class artifact and binds the exact diff SHA-256 to exact base/head commit SHAs.
- Verification is explicit; an unrun verification is recorded as `NOT_RUN`, never inferred as pass.
- Auto-merge is always false in repair metadata.
- A failed or unknown repair remains a repair proposal; it is not silently promoted.

## Artifact contract

A repair run should retain:

- `WORKFLOW_FAILURE_ANALYSIS.json`
- `WORKFLOW_REPAIR_PLAN.json`
- `repair.diff`
- `WORKFLOW_REPAIR_VALIDATION.json`
- `WORKFLOW_REPAIR_EVIDENCE.json`
- verification output, when verification is actually run

The evidence artifact uses schema `autobot-repair-diff-evidence/v1` and binds:

- diff SHA-256, byte count, touched files, file count, and hunk count
- exact base ref + 40-character base commit SHA
- exact head ref + 40-character head commit SHA
- validation status and validation errors
- application status and task-branch target
- `apply_to_main=false` and `auto_merge=false`
- explicit verification status and optional verification reference

Evidence creation rejects a mismatched diff hash, inconsistent validation metadata, invalid commit SHAs, and an unrun verification that claims a verification reference.

## CLI

Validate an existing proposal:

`python tools/repair_diff_pipeline.py --diff reports/repair.diff --output reports/WORKFLOW_REPAIR_DIFF_VALIDATION.json`

Generate a bounded proposal without changing the working tree:

`python tools/repair_diff_pipeline.py --generate main --head HEAD --output reports/WORKFLOW_REPAIR_DIFF_VALIDATION.json`

The generated diff should be saved as `reports/repair.diff`, reviewed, and validated again before application.

Explicitly apply a validated proposal on the current task branch:

`python tools/repair_diff_pipeline.py --diff reports/repair.diff --apply`

Build tamper-evident evidence after validation:

`python tools/repair_diff_evidence.py --diff reports/repair.diff --validation reports/WORKFLOW_REPAIR_DIFF_VALIDATION.json --base-ref main --base-sha <BASE_SHA> --head-ref HEAD --head-sha <HEAD_SHA> --output reports/WORKFLOW_REPAIR_EVIDENCE.json`

Record verification only after it has actually run:

`python tools/repair_diff_evidence.py --diff reports/repair.diff --validation reports/WORKFLOW_REPAIR_DIFF_VALIDATION.json --base-ref main --base-sha <BASE_SHA> --head-ref HEAD --head-sha <HEAD_SHA> --verification-status PASS --verification-ref <VERIFICATION_REF> --output reports/WORKFLOW_REPAIR_EVIDENCE.json`

`--apply` is intentionally unavailable together with `--generate`, preventing a generated proposal from being applied in the same step.

The tools do not push or merge. Promotion remains governed by the existing branch, release, provenance, and approval gates.
