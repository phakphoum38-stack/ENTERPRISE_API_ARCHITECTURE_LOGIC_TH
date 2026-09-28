# Research OS H22 — Learned Skill Registry Boundary

## Contract

H22 is the governed materialization boundary between an explicit H10 promotion receipt and the existing learned-skill registry.

```text
H21 PROMOTION RECORD
        │
        ▼
   H10 PROMOTION
        │
        ▼
H10 PROMOTION RECEIPT
        │
        ▼
H22 LEARNED SKILL REGISTRY
```

H22 never decides whether a candidate should be promoted. It accepts only an explicit H10 receipt whose authority and fingerprints are valid.

## Required invariants

- Receipt schema: `research-os-learning-promotion-receipt/v1`.
- `promotion_authority` must be `H10`.
- `approved` must be true.
- `read_only` remains true and `authority` remains `none` in the receipt contract.
- H21 promotion-record fingerprint must match exactly.
- Receipt fingerprint is recomputed before registry materialization.
- Candidate payload is bounded and scanned for unsafe execution, credential, release, merge, install, dispatch, and bypass content.
- Materialization uses the existing `LearnedSkillRegistry`; the core `SkillRegistry` is never mutated by this boundary.

## Authority

H22 is not a promotion authority. H10 remains the sole authority that can produce an approved promotion receipt.

H22 cannot approve candidates, choose promotion outcomes, execute skills, release/install artifacts, merge PRs, dispatch workflows, mutate refs, or rewrite evidence.

## Evidence

The H22 Python tests are the executable contract. CI is authoritative. This document is design context only.
