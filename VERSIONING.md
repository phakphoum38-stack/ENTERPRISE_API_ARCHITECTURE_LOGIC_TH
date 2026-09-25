# Versioning Policy

## Current baseline

`v0.3.0-alpha` — Durable Execution Foundation.

## Product release line

- `v0.1.x` — Foundation
- `v0.2.x` — Runner Fleet
- `v0.3.x` — Durable Execution
- `v0.4.x` — Production Queue
- `v0.5.x` — HA / Scale
- `v0.6.x` — Enterprise hardening
- `v1.0.0` — Production Stable

## Rules

We use Semantic Versioning for release tags. Breaking public API changes require a major version. Backward-compatible features use a minor version. Bug fixes use a patch version.

API versions are independent from product versions and use explicit paths such as `/api/v1/...`.

Database changes are migration-based and must be ordered, reviewable, and reversible where practical.

Release artifacts should include `VERSION`, `CHANGELOG.md`, release notes, and migration notes when applicable.
