# Generate Repair Branch

When a registered downstream stage fails, the Generate Orchestrator should not continue silently or mutate `main`.

Recovery contract:

1. Stop at the failed stage.
2. Create a dedicated repair branch from the exact `main` commit used by the orchestrator run.
3. Record the failed stage, workflow, run ID, commit SHA, and failure classification on that branch.
4. Apply generated/source fixes only on the repair branch.
5. Re-run preflight validation on the repair branch.
6. Open a PR back to `main` only after validation passes.
7. Resume the failed stage from the repaired branch; do not restart already-passed stages unless explicitly requested.

The repair branch is evidence-preserving and must never force-push or mutate `main` directly.
