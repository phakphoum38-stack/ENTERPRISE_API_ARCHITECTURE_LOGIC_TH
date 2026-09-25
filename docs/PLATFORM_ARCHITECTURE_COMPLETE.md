# Platform Architecture: Complete Composition Boundary

The Platform is the reusable root. Research OS is a product surface on that
Platform, and external tools are observation/integration inputs rather than
Platform authority.

## Canonical composition

- Discovery: M.2 Platform service.
- Graph: existing Platform Graph.
- Project identity: existing Project Registry.
- Execution: existing Queue, Worker Pool and Stateless Runner.
- Evidence: existing evidence/provenance plane.
- Governance: existing governance validators.
- Release: Unified Final Gate.

No second scheduler, queue, worker pool, runner, evidence ledger,
authorization authority, navigation registry or release authority is introduced.

## Continuity

The portable snapshot preserves source SHA, active/deferred work, decisions,
verified truths, evidence references and authority boundaries. A successor AI
must verify SHA and reconcile current Platform state before mutation.

## Safety

Unknown, stale, conflicting or missing state remains fail-closed. Deferred work
is preserved and is never silently promoted to completion.
