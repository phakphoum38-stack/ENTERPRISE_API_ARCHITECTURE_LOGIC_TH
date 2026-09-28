# P0-05 Provenance Conformance Suite

This suite defines executable expectations for provenance implementations.

## Mandatory cases

- valid typed Git SHA-1 identity for a Git commit
- valid SHA-256 artifact identity
- Git SHA-1 used as artifact SHA-256 → reject
- wrong algorithm → reject
- truncated/padded digest → reject
- modified canonical object → reject
- target commit mismatch/stale evidence → reject
- sequence gap/duplicate ID → reject
- broken previous-entry link → reject
- unknown evidence/attestation reference → reject
- caller-supplied derived fields → reject

## Required properties

1. Same canonical input + same algorithm + same version → same digest.
2. Any meaningful identity/content mutation → verification failure.
3. Canonical JSON ordering/whitespace changes that are semantically irrelevant → same digest.
4. Git object identity never substitutes for artifact/content identity.
5. Unknown security-critical semantics fail closed.

The current executable regression suite is `tools/test_validate_provenance_evidence.py`. This directory is the stable home for future fixture expansion, property-based tests, mutation tests, and differential implementations.
