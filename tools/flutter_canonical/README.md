# Canonical Flutter Toolset

This directory is the canonical, deduplicated engineering toolset imported from `phakphoum38-stack/flutter` `main`.

## Included

- `contract_checker/main.py` — repository contract marker validation.
- `version_validator/main.py` — Flutter/Dart semantic application version validation.
- `workflow_validator/main.py` — conservative GitHub Actions workflow validation.
- `security_scanner/main.py` — advisory secret-like pattern scanning.

## Deduplication rule

These tools are kept under one canonical namespace. Existing repository tools with overlapping responsibility remain the source of truth; no parallel copy is created when an equivalent capability already exists.

The upstream Flutter README also mentions `repo_inspector`, but the current upstream `main` tree does not contain that tool, so the stale reference is intentionally not copied.

## Skills

Application skills already present in the enterprise repository remain canonical. The Flutter repository does not currently expose a separate `skills/` tree on `main`; therefore no duplicate skill package is invented here.

## Safety

- No workflow is added or changed by this tool import.
- Tools are reporting/validation utilities and are not part of the Flutter runtime.
- Promote a tool to a hard gate only after its tests and false-positive behavior are reviewed.
