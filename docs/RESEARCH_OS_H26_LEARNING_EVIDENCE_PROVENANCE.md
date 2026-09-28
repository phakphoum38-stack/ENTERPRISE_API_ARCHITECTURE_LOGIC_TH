# Research OS H26 — Learning Evidence / Provenance Binding

## Contract

H26 binds externally supplied evidence references to an H25 executor-result envelope without fabricating, approving, or executing evidence.

```text
H25 EXECUTOR RESULT
        │
        ▼
H26 EVIDENCE / PROVENANCE
        │
        ▼
H27 FINAL LIFECYCLE
```

## Required invariants

- H25 schema must be `research-os-learning-executor-result/v1`.
- Executor result must remain read-only with no independent authority.
- Owner, source SHA, skill name/version, correlation ID, and executor-result fingerprint must match exactly.
- At least one externally supplied evidence reference is required.
- Evidence references are bounded and scanned for unsafe control/execution content.
- Evidence is referenced, not fabricated by H26.
- Output schema is `research-os-learning-evidence-provenance/v1`.
- Final lifecycle authority is explicitly deferred to H27.

## Authority boundary

H26 cannot approve promotion, execute skills, release/install artifacts, merge PRs, dispatch workflows, mutate refs, or rewrite evidence.

## Evidence

The H26 Python tests are the executable contract. CI is authoritative. This document is design context only.
