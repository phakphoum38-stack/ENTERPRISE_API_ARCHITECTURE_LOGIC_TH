# AEOS Open-Ended Assurance Universe

## Purpose

AEOS is designed as an extensible assurance fabric, not a fixed checklist. New assurance universes, planes, domains and controls may be declared without changing the core engine. The trust boundary remains fixed.

## Scale model

The model is intentionally unbounded:

```text
Universe → Plane → Domain → Control → Dimension → Evidence → Verification → Certification
```

A large deployment may model 100, 1,000, 100,000 or more assurance cells. The number is an outcome of the ontology and system reality, not a constitutional limit.

## Immutable trust rules

1. UNKNOWN is never PASS.
2. NOT_OBSERVED is never PASS.
3. STALE evidence cannot certify current state.
4. CONFLICT cannot certify current state.
5. Self-attestation is not independent evidence.
6. Evidence does not grant authority.
7. Verification is not certification.
8. Certification is not merge.
9. Merge is not completion.
10. Discovery is not authorization.
11. Autonomous execution cannot modify the constitutional trust anchor.
12. A new assurance control must declare scope, risk, evidence, verification and recovery requirements.

## Assurance cell

Every control is a proof obligation, not a boolean flag. A cell should be able to answer:

- What is being assured?
- Which scope is covered?
- What authority is relevant?
- What evidence is required?
- Where did the evidence originate?
- How fresh is it?
- Which independent verification mode was used?
- What happens on UNKNOWN, STALE or CONFLICT?
- How is failure recovered?
- What certificate binds the final result?

## Open-ended extension

The fabric compiler accepts declarative controls and produces typed assurance primitives. It does not certify implementation. Concrete scanners, repository adapters, CI adapters, runtime observers and governed certifiers remain separate boundaries.

```text
Discovery
  ↓
Declaration
  ↓
Contract
  ↓
Observation
  ↓
Evidence / Provenance
  ↓
Independent Verification
  ↓
Certification
```

A newly discovered object therefore enters UNKNOWN/quarantine until it has a contract and proof path.

## Assurance debt

Coverage is measurable as debt rather than hidden:

- assurance debt
- evidence debt
- verification debt
- risk debt
- governance debt

These are first-class states that prevent an empty queue from being mistaken for a complete system.

## Reality boundary

Declared state is not reality. AEOS must distinguish:

```text
DECLARED → OBSERVED → VERIFIED → CERTIFIED
```

Post-merge verification therefore remains separate from merge success.

## Meta-assurance

AEOS may inspect its own consistency, coverage and drift, but self-observation cannot become self-certification. Independent verification and governance remain outside the autonomous execution boundary.

## Implementation status

This document defines the extensible architecture. Current implementation adds pure, side-effect-free boundaries for authority/risk, semantic diff, blast radius, decision replay, post-merge verification, and the open-ended assurance registry/compiler. Concrete external reality scanners are deliberately adapter work and are not fabricated by this foundation layer.
