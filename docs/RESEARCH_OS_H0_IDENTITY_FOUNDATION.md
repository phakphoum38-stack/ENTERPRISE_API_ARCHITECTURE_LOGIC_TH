# Research OS H0 — Identity Foundation

**Status:** IMPLEMENTATION DRAFT — verification required
**Base:** `42b87670a9ce10d66f53a53a321b35b800057e18` (canonical 4H)
**Branch:** `feat/h0-identity-foundation`

## Purpose

Establish a small, side-effect-free identity layer that prevents a verification pipeline from silently switching source SHAs.

## Contract

1. `WAITING_FOR_SHA` means identity has not been captured and is pending.
2. `CAPTURED` records the intended SHA and is never a pass result.
3. Every downstream verification step binds to the captured SHA.
4. A different observed SHA becomes `SHA_MISMATCH` and cannot be treated as success.
5. A verification result can only be produced after `CAPTURED -> VERIFYING`.
6. A code change creates a new SHA and therefore requires a new capture and new verification.
7. Evidence without a valid `commit_sha`, or evidence bound to another SHA, is stale/unsafe.
8. Waiting is bounded; exhausted waiting becomes `TIMEOUT`.
9. Lineage identifiers are deterministic and derived from the source SHA plus ordered stages.
10. The module does not dispatch workflows, modify refs, approve, release, install, or persist mutable evidence.

## Initial implementation

- `owner_special/research_os_friend/identity_foundation.py`
- `owner_special/tests/test_identity_foundation.py`

The implementation is intentionally independent of workflow execution. Authoritative CI must verify the branch before this contract is considered implemented.

## Intended next integration

After H0 unit validation, add the exact-SHA binding to the authoritative workflow/gate layer without allowing Workflow Intelligence or Mission Control to become identity authority.

## Non-goals

- no workflow auto-dispatch
- no auto-merge
- no release/install
- no generated evidence fabrication
- no capability escalation
