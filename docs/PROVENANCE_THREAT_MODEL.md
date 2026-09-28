# P0-05 Provenance Threat Model

## Security objective

Prevent a provenance claim from being accepted unless the exact identity, canonical representation, derivation, target context, and evidence lineage are independently verified.

## Threat → invariant → regression

| Threat | Required invariant | Regression |
|---|---|---|
| Git SHA-1 substituted for artifact SHA-256 | Git and artifact identities are typed and non-interchangeable | `test_git_sha1_is_never_accepted_as_artifact_sha256` |
| Truncated/padded digest | Exact algorithm length and value | `test_wrong_digest_length_is_rejected_without_normalization` |
| Wrong algorithm | Explicit allowlist; no inference | typed digest validation |
| Modified artifact/evidence | Recomputed digest/entry hash must match | payload tamper test |
| Stale evidence | Evidence target revision must match the verification context | target binding tests |
| Wrong repository/path/context | Identity and location are separate; context is explicit | conformance fixtures |
| Replay | Entry IDs, sequence, target revision and future event identity must be unique | planned replay suite |
| Producer self-approval | Producer emits claims; verifier emits authoritative result | trust contract |
| Shared producer/verifier bug | Independent verification path | verifier is separate from producer |
| Canonicalization drift | Versioned deterministic UTF-8 canonicalization | deterministic fixtures |
| Cross-platform divergence | Same canonical bytes produce same digest | planned cross-platform suite |
| Silent downgrade | No implicit algorithm/contract downgrade | contract policy |
| Unknown critical fields | Fail closed at security boundary | schema-evolution policy |
| Ledger reordering/deletion | Contiguous sequence and previous-entry hash | chain/sequence tests |
| Hash collision across contexts | Domain separation | domain-separated entry hashing |

## Trust boundaries

```text
Producer assertion
      ↓ untrusted
Evidence / Ledger
      ↓
Independent verifier
      ↓ trusted verification result
Policy gate
      ↓
Merge / Release acceptance
```

## Non-goals

P0-05 does not grant authority, replace human approval, or claim that a hash chain alone provides authorization. Cryptographic integrity and authorization are separate concerns.

## Future controls

Replay counters, immutable storage/sealing, Merkle roots, property-based testing, mutation testing, and differential verification are extension points. They must preserve the core fail-closed invariants and cannot weaken identity or derivation checks.
