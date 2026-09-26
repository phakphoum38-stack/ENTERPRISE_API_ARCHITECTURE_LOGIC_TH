# Laravel Platform Runbook V1

## Build order

1. Keep the branch based on current main.
2. Validate contracts before runtime implementation.
3. Implement one bounded module at a time.
4. Reuse existing Research OS capabilities through adapters.
5. Add tests and evidence with each module.
6. Run the applicable Final Gate before merge.

## Change rule

Inspect -> identify missing capability -> reuse -> modify only the missing capability -> validate -> Final Gate -> PR -> merge.

## Failure rule

A failed authorization, entitlement, version check, integrity check or resource-conflict check fails closed. No fallback silently grants execution.

## Release rule

The Laravel Platform is not release-complete until its required contracts, integration tests, security boundary tests, operational checks and Unified Final Gate checks are satisfied.
