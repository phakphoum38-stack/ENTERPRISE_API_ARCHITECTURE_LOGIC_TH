# PR #41 ↔ PR #47 Compatibility Gate

Status: CONDITIONAL PASS

## Boundary decision

- `127.0.0.1:8787` = Research OS Main API / ServiceHost.
- `127.0.0.1:8790` = Owner Friend + V3 10^10 production boundary.
- Existing `8788` references are treated as legacy V3 references until individually classified.
- Do **not** perform a global `8788 -> 8790` replacement.

## Validation rules

1. Preserve the V3 Unified Master as the scale authority.
2. Keep logical 10^10 helper capacity bounded by queue/backpressure; do not create 10^10 physical workers.
3. Require loopback-only listeners for 8787 and 8790.
4. Keep V1/data-preservation behavior unchanged.
5. Validate the current `apps/research_os_flutter` GUI against the unified stack.
6. Require clean-install, GUI launch, 10^10 status, loopback, upgrade, artifact and SHA256 evidence before changing PR #47 from Draft.

## Evidence from PR #47

The unified Windows gate already probes:

- `http://127.0.0.1:8790/owner/health`
- `http://127.0.0.1:8787/health`
- `http://127.0.0.1:8790/owner/status`

and verifies the V3 unified master, 10^10 logical capacity, loopback binding, GUI launch, upgrade, and SHA256 artifact.

## Decision

No runtime source change is made by this compatibility pass. The legacy 8788 references must remain isolated from the production 8790 boundary unless a specific runtime contract requires migration.
