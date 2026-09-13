# H20 — Learning Promotion Eligibility Boundary

## Purpose

H20 classifies whether an H19 integrity-verified learning candidate is eligible to enter the existing H10 promotion authority.

## Boundary

`H19 INTEGRITY VERIFIED → H20 PROMOTION ELIGIBILITY → H10 PROMOTION AUTHORITY`

H20 is a read-only classifier. It does not promote, approve, execute, release, merge, install, dispatch, mutate refs, or rewrite evidence.

## Required invariants

- exact Owner/source SHA/correlation/skill fingerprint/result fingerprint binding
- exact candidate version and H19 binding fingerprint
- H19 integrity must be verified
- promotion authority remains `H10`
- `read_only=true` and `authority=none`
- explicit evidence verification is required for eligibility
- quality score is bounded to `[0, 1]`; the eligibility threshold is `0.8`
- unsafe candidate content is rejected with bounded recursive scanning
- output is detached and deterministically fingerprinted

## Decisions

- `ELIGIBLE_FOR_H10`: evidence is verified and quality score is at least `0.8`
- `NOT_ELIGIBLE`: evidence is missing or quality is below the threshold

An H20 eligibility result is not a promotion result. H10 remains the sole promotion authority already established by the existing learning promotion policy.

## CI authority

GitHub Actions remains authoritative. Generated evidence and release artifacts must come from the existing workflows; this document is not evidence of a passing run.
