# Research OS External Validation Plane

The External Validation Plane is the platform's read-only validation boundary for an exact repository SHA.

## Purpose

GitHub Actions remains the required Final Gate and merge/release authority. The external plane provides an independent validation path when CI infrastructure is unavailable, delayed, or cannot produce usable step evidence.

It is not a second release authority.

## Pipeline

exact source SHA
  -> External Validation Plane
  -> Platform Recon
  -> Self-Reconciliation
  -> Platform Governance
  -> Canonical Security Validation
  -> deterministic evidence
  -> Assurance / M2 consumption
  -> GitHub Final Gate
  -> merge / release

## Invariants

- The input SHA must exactly match checked-out HEAD.
- Validators are existing canonical platform capabilities; the runner is orchestration, not a new authority.
- Results are evidence projections only.
- Non-zero validator results fail closed.
- Unknown or unavailable validation must not be converted to PASS.
- Any path containing the excluded EFI path segment remains outside the scan boundary.
- The runner never changes source, approves pull requests, merges pull requests, or releases artifacts.
- GitHub Final Gate remains the only merge/release authority.

## Run

From the exact workstream checkout:

    python tools/external_validation.py --source-sha <EXACT_SHA>

Evidence is written to:

    evidence/external-validation.json

The evidence records the exact source SHA, contract digest, validator decisions, and authority boundary.

## M2 relationship

M2 remains the indexing, recon, relationship, and evidence context layer. The External Validation Plane consumes existing M2-compatible surfaces rather than creating another graph, registry, queue, authorization engine, or release authority.
