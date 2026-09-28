# Research OS Architecture Completeness

Status: **ACTIVE / READ-ONLY INSPECTION**

The architecture is treated as complete only when the canonical contract,
shared boundaries, implementation roots, verification controls, and release
lineage are all explicit. Existing capabilities are not duplicated merely to
make the matrix look complete.

## Canonical model

```text
Three Flutter roots
      |
      v
Shared Contracts
      |
      +--> Navigation / State / Error / Control
      +--> Observability / Schema / Platform / Migration
      +--> Lifecycle / Capability
      |
      v
Adapters
      |
      v
Runtime / API / Provider / GitHub / Friend
      |
      v
Verification
      |
      v
Evidence + Provenance
      |
      v
Release / Upgrade / Retirement
```

The canonical presentation shell remains `owner_special/flutter_app`.
The other roots remain compatibility/application surfaces until parity and
retirement gates are independently satisfied.

## Completeness dimensions

The machine-readable contract covers:

- contract and ownership
- implementation and adapter boundaries
- UI and API surface mapping
- state and navigation
- error/recovery
- security and human authority
- audit/observability
- offline recovery
- idempotency/concurrency
- schema/version compatibility
- platform parity
- design system and accessibility
- performance budgets
- feature-flag lifecycle
- artifact provenance
- migration/rollback
- retirement

## Inspector

Run locally from the repository root:

```bash
python tools/validate_architecture_completeness.py
```

Optional machine-readable output:

```bash
python tools/validate_architecture_completeness.py --json-out architecture-completeness.json
```

The inspector is intentionally **read-only**. It does not:

- edit source code;
- change branches or commits;
- run workflows;
- merge pull requests;
- grant authority;
- rewrite Git history.

## Interpretation

- **PASS** — all required structural controls are present.
- **FAIL** — a required control is absent or the registry is inconsistent.
- **UNKNOWN is not PASS** — semantic behavior still requires the appropriate
  unit, integration, E2E, provenance, platform, and human-authority gates.

This inspector therefore closes the architecture-governance gap without
pretending that file presence alone proves runtime behavior.

## Change rule

New capabilities must first declare:

1. canonical owner;
2. shared contract;
3. implementation boundary;
4. adapter/API mapping;
5. state and error semantics;
6. authority/security boundary;
7. observability/evidence path;
8. compatibility and migration policy;
9. verification coverage;
10. retirement condition.

Only then should the capability be surfaced in a canonical UI.

## Safety invariant

Architecture generation may propose or create changes, but verification remains
exact and independent. `READY_FOR_OWNER_AUTHORITY` is not merge authorization.
No automatic merge, authority grant, or history rewrite is part of this system.
