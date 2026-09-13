# P0-06 Policy-as-Code Gate Engine

## Purpose

P0-06 is the deterministic enforcement layer between the existing constitutional, identity/authority, and provenance contracts and downstream execution systems.

```text
EC-001 Constitution
       +
IAC-001 Identity / Authority
       +
PEC-001 Provenance / Evidence
       |
       v
Policy Source
       |
       v
Deterministic Compiler
       |
       v
Gate Plan
       |
       v
Fail-Closed Evaluator
       |
       +---- PASS
       +---- BLOCK
       +---- REQUIRE_APPROVAL
       |
       v
Evidence Receipt
```

## Authority boundary

P0-06 does **not** create authority. The compiler only validates and normalizes policy. The evaluator only evaluates supplied evidence. Neither component may:

- grant a capability;
- change ownership;
- replace `OwnerPolicy`;
- replace `ApprovalGate`;
- execute a runtime action; or
- silently turn unknown evidence into approval.

The existing authority chain remains authoritative:

```text
UI intent
  -> FriendOrchestrator (execution authority)
  -> OwnerPolicy (authorization authority)
  -> ApprovalGate (approval authority)
  -> execution
  -> evidence / trace
```

## Fail-closed semantics

Evidence states are `VERIFIED`, `REJECTED`, `UNKNOWN`, `MISSING`, and `STALE`.

`UNKNOWN`, `MISSING`, `STALE`, and `REJECTED` are blocking states. Absence of evidence is therefore never interpreted as permission.

Core invariants:

- UNKNOWN is not PASS.
- Missing evidence blocks.
- Revoked authority blocks.
- Expired delegation blocks.
- Scope escalation blocks.
- Wildcard scope blocks.
- Missing authorization proof blocks.
- Conflicting authority blocks.
- Expired exceptions block.
- Exceptions cannot escalate authority.
- Policy versions and fingerprints are reproducible.
- Identical policy/input/evidence produces the same evaluation fingerprint and decision.
- Every decision carries the policy and compiled-plan fingerprints needed for evidence correlation.

## Determinism

Policy fingerprints use SHA-256 over canonical UTF-8 JSON with sorted object keys and compact separators. The compiled plan is likewise fingerprinted.

Evaluation receipts exclude wall-clock time from the evaluation fingerprint. This prevents timestamps from making identical evaluations appear different.

## Exception model

An exception, when introduced by a future policy fixture, must be explicit, scoped, justified, approved, time-bounded, and evidenced. An expired or unverifiable exception is blocking. An exception cannot grant authority that the underlying identity/authority contract does not provide.

## CI enforcement

`.github/workflows/policy-gate.yml` validates the canonical contract, executes negative and determinism tests, compiles the canonical fixture, and verifies that the compiled plan has no authority effect.

## Handoff

After this gate engine is verified, #324 may consume its deterministic decision/proof boundary for the Agent Mesh. #324 must not introduce a parallel policy or authority engine.
