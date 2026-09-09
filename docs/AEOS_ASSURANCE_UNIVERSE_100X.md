# AEOS Assurance Universe 100X

## Purpose

AEOS does not treat a large assurance catalog as thousands of hand-maintained checks. It defines a deterministic address space from reusable domains, assurance families, dimensions, and lifecycle phases. An address is a question that requires reality evidence; it is never evidence by itself.

The current global universe contains 120 assurance domains. The 100X contract adds exactly 100 reusable assurance families and 100 assurance dimensions, with 16 lifecycle phases. This yields a generated address space of:

`120 × 100 × 100 × 16 = 1,920,000` possible assurance addresses.

This is an address-space target, not a claim that all addresses are applicable, observed, verified, or certified.

## Constitutional rules

- `ASSERTED` is not `VERIFIED`.
- `OBSERVED` is not `CERTIFIED`.
- `VERIFIED` is not `MERGED`.
- `CERTIFIED` is not `COMPLETED`.
- `DISCOVERED` is not `AUTHORIZED`.
- `UNKNOWN`, `NOT_OBSERVED`, `STALE`, `CONFLICT`, `UNCLASSIFIED`, and `QUARANTINED` never pass.
- Generated addresses cannot manufacture evidence.
- Generated addresses cannot grant authority.
- Generated addresses cannot certify themselves.
- Main SHA, policy, contract, verifier, oracle, or evidence-root changes invalidate dependent proof until rebound and reverified.
- Novel conditions enter the novelty firewall.
- Common-mode dependencies are tracked separately from evidence count.
- Unknown-budget exhaustion, mutation escape, failed canaries, and ungoverned bypass surfaces block certification.

## Conservation laws

AEOS treats the following as invariant properties across the lifecycle:

1. identity continuity
2. authority non-escalation
3. evidence temporal causality
4. intent continuity
5. provenance continuity
6. causal ordering
7. policy binding
8. state-transition integrity
9. trust non-reuse
10. uncertainty preservation

## Assurance address

Every generated assertion is identified by a deterministic hash-derived identifier:

`domain × family × dimension × lifecycle → assertion_id`

The compiler in `tools/aeos_assurance_universe_compiler.py` performs only enumeration and vocabulary validation. It does not observe the repository, produce evidence, verify reality, or issue certificates.

## Lifecycle

`DECLARE → IDENTIFY → OBSERVE → VALIDATE → BIND → VERIFY → AUTHORIZE → EXECUTE → PROVE → CERTIFY → PROMOTE → DEPLOY → MONITOR → RECOVER → REPLAY → REBASELINE`

A missing observation remains missing. A novel condition remains novel until an independent boundary resolves it.

## Verification strategy

The universe is intended to be paired with concrete reality adapters and independent verifiers. The address space itself is deliberately not a scanner. This preserves the distinction between:

`contract → observation → evidence → provenance → independent verification → certification`

That separation is consistent with SLSA's model: provenance identifies how an artifact was produced, and consumers verify provenance against expectations; stronger levels increase authenticity, accuracy, and isolation requirements. citeturn0search0turn0search4

## Supply-chain continuity

The same model applies across source, build, artifact, package, promotion, deployment, and recovery. Source provenance should provide contemporaneous, tamper-resistant history, while build provenance should identify the artifact and production process. citeturn0search1turn0search8

## Non-goals

This document does not claim:

- 1,920,000 runtime checks exist today;
- every address is applicable to every mission;
- a generated catalog is proof of repository state;
- declarative contracts are equivalent to executable verification;
- CI has been executed by this change pass.

Concrete verification remains a separate, evidence-producing implementation boundary.
