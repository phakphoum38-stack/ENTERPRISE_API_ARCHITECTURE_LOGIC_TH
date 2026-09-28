# AEOS Source-Level Test Matrix

This matrix is generated from `current/AEOS_ASSURANCE_CHECK_REGISTRY.json` and is intentionally fail-closed.

| Result | Meaning | Certification |
|---|---|---|
| SOURCE_VERIFIED | Real executable source boundary traced for the check | Eligible after independent evidence and regression proof |
| SOURCE_GAP | Required source test has no executable boundary | Blocks certification |
| SOURCE_INVALID | Boundary exists but cannot be shown to implement the named check | Blocks certification |
| EXTERNAL_EVIDENCE | Check is an external/evidence obligation, not a local source test | Blocks certification until independent evidence is bound |

The source-level validator is authoritative for this matrix. A green registry-integrity check must not override a source gap.
