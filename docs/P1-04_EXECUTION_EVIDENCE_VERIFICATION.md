# P1-04 Execution Evidence → Verification Binding

## Purpose

Bind the existing resource execution result and existing forensic evidence
record into one immutable verification projection under the canonical
mission/work/baseline lineage.

## Existing authorities remain unchanged

- Resource Control Plane owns admission, reservation, routing, accounting, ledger and resource evidence.
- Forensic evidence owns forensic provenance and source references.
- AEOS remains the durable work graph and verification authority.
- This adapter does not create a queue, scheduler, worker, retry engine, or authority path.

## Correlation

`CanonicalIdentity` → `ResourceExecutionBinding` → `ForensicEvidence` → `ExecutionEvidenceBinding`

The resulting binding carries deterministic SHA-256 hashes and evidence
references so downstream verification can correlate existing records without
reconstructing identity from provider payloads.

## Fail-closed rules

1. Resource binding must match the exact canonical identity.
2. Forensic evidence must match mission/work/baseline.
3. Resource and provenance binding hashes must be SHA-256.
4. Verification status is required.
5. Verification fingerprint must be a SHA-256 digest.
6. Cross-lineage verification is rejected.

This is a correlation/projection boundary only. It does not declare subject
truth, authorize a repair, or authorize merge.
