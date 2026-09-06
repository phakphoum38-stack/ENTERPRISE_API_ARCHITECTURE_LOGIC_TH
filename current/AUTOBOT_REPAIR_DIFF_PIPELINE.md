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
- Auto-merge is always false in repair metadata.
- A failed or unknown repair remains a repair proposal; it is not silently promoted.
- Evidence should record the diff SHA-256, base/head refs, touched files, validation result, application result, and verification run.

## Artifact contract

A repair run should retain:

- `WORKFLOW_FAILURE_ANALYSIS.json`
- `WORKFLOW_REPAIR_PLAN.json`
- `repair.diff`
- `WORKFLOW_REPAIR_VALIDATION.json`
- verification output

The diff hash binds the proposed change to the evidence record.

## CLI

Validate an existing proposal:

`python tools/repair_diff_pipeline.py --diff reports/repair.diff --output reports/WORKFLOW_REPAIR_DIFF_VALIDATION.json`

Generate a bounded proposal without changing the working tree:

`python tools/repair_diff_pipeline.py --generate main --head HEAD --output reports/WORKFLOW_REPAIR_DIFF_VALIDATION.json`

The generated diff should be saved as `reports/repair.diff`, reviewed, and validated again before application.

Explicitly apply a validated proposal on the current task branch:

`python tools/repair_diff_pipeline.py --diff reports/repair.diff --apply`

`--apply` is intentionally unavailable together with `--generate`, preventing a generated proposal from being applied in the same step.

The tool does not push or merge. Promotion remains governed by the existing branch, release, provenance, and approval gates.
