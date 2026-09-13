# H3 Automation Readiness Matrix

**Base SHA:** `c04d60b36d51eb8529a4c65a61c7d5a411e5fe85`
**Mode:** `AUTO_GUARDED`
**Auto-merge:** `DISABLED`

| Boundary | Requirement | H3 control |
|---|---|---|
| Identity | Exact source SHA | `expected_sha` is validated and propagated |
| Lineage | H2 evidence binding | Snapshot must declare H2 evidence schema |
| Ownership | Owner isolation | Snapshot owner must equal requested owner |
| Presentation | Read-only | `read_only=true` is mandatory |
| Authority | Fixed authority declarations | Execution/authorization/approval authorities are exact |
| Safety | Dynamic/action content | Blocked key scan and bounded traversal |
| Determinism | Stable fingerprint | Canonical JSON + SHA-256 |
| Unknown/stale | Fail closed | Schema, owner, SHA, and evidence mismatches reject |
| Automation | Guarded only | Assessment cannot execute, approve, release, merge, or dispatch |
| Governance | Self-judgment protection | Contract is external to the assessment result |

## Promotion gate

H3 may be promoted toward autonomous merge only after exact-head CI, adversarial regression, evidence/provenance verification, authority audit, and post-merge verification are independently green. A green test result alone does not grant merge authority.
