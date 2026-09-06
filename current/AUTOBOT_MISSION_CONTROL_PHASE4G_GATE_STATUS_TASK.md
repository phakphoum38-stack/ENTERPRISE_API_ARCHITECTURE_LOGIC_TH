# Autobot Mission Control Phase 4G — Gate Status Projection Task

## Objective
Add a deterministic, bounded, read-only projection of authoritative Research OS release/gate status for Mission Control.

## Requirements
- Consume existing authoritative gate evidence only.
- Never execute, dispatch, retry, approve, override, mutate, or reinterpret a gate.
- Represent PASS / FAIL / PENDING / UNKNOWN explicitly.
- Preserve exact workflow/check identity and commit SHA where evidenced.
- Fail closed on conflicting or malformed evidence.
- Owner-scoped, deterministic, bounded, and safe for UI consumption.
- Reuse Phase 4D UI schema validation.

## Safety
No workflow execution, release mutation, authorization, approval, policy change, persistence, network side effects, tool/MCP/browser/Computer Use execution, credentials, or secrets.

## Tests / evidence
Test complete, failed, pending, unknown, conflicting, stale, oversized, and nondeterministic gate payloads. Produce clean `.diff` and machine-readable evidence artifacts with exact lineage and authority audit.

## Workflow discipline
Do not manually dispatch workflows or merge. Normal CI remains the verification mechanism; merge is an owner-controlled action after all authoritative gates pass.
