# Candidate Build Policy

Research OS uses a write-first, validate-by-exact-SHA candidate workflow.

## Canonical rule

- Normal development commits do not automatically consume GitHub Actions.
- Run local preflight first with `scripts/research-os-preflight.ps1`.
- Use `ci-lite.yml` manually only when additional GitHub-hosted Python/API or Flutter evidence is useful.
- `candidate.yml` registered on `main` is the canonical owner of Windows release-candidate validation.
- A feature branch must not create or maintain a second copy of `candidate.yml`.
- Candidate validation is started manually with the exact target commit SHA.
- One candidate SHA should produce one intentional candidate run unless a failed run requires a justified retry.

## Candidate responsibilities

The canonical candidate workflow owns the release-grade Windows chain:

1. API and software-factory tests
2. Flutter Windows build and tests
3. ServiceHost publish
4. Runtime and Windows Service smoke tests
5. Setup EXE build
6. Clean install validation
7. In-place upgrade validation
8. Data-preservation validation
9. Loopback/security/provider-status checks
10. Exact-SHA manifest and SHA256 evidence
11. Verified candidate artifact upload

Release and merge remain separate explicit actions and are never implied by Candidate success.

## Other artifact workflows

`artifacts-build.yml` may be used manually to create website, Windows, or unsigned iOS distribution/developer artifacts for an exact SHA.

Those outputs are not verified release-candidate evidence and must not replace the lineage produced by `candidate.yml` when publishing a Release.

`browser-use-cloud-smoke.yml` is also manual-only. Its default mode uses the local Browser Use simulator; real cloud validation is opt-in and requires the GitHub Secret `BROWSER_USE_API_KEY`.

## Removed legacy behavior

The repository no longer relies on:

- automatic push-triggered candidate builds,
- a `[candidate]` commit-message marker,
- chained workflow-to-workflow dispatch for candidate construction,
- multiple independent Windows installer workflows.

This policy keeps normal development at zero automatic Actions usage while preserving one canonical exact-SHA candidate evidence path.
