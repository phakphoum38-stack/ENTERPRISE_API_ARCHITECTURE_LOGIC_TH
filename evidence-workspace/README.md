# Research OS Evidence Workspace

Virtual evidence workspace for Research OS CI gates.

## Purpose

This workspace records the **structure and state** discovered from GitHub and CI execution without fabricating runtime results.

- `pending` means the stage has not produced runtime evidence yet.
- `running` means execution has started.
- `passed` means the runtime gate produced actual evidence.
- `failed` means the runtime gate produced an actual failure.
- `skipped` means the stage was intentionally not executed.

The workspace is separate from runtime owner data and does not contain credentials or secrets.

## Current pipeline

`YAML → Exact-SHA → Flutter → 8787 → 8788 → 10×10 → 8790 → Evidence/SHA256 → PR #49`

## Source of truth

Repository structure, commit SHA, workflow/job metadata, and actual CI results come from GitHub. This repository directory is only the persistent workspace for the generated state model.
