# Autobot Mission Control Phase 5B — Desktop State Model Task

## Objective
Define a deterministic UI state model for Mission Control so the desktop shell never converts missing/unknown runtime information into implied success.

## State contract
Support explicit states:
- `EMPTY`
- `LOADING`
- `READY`
- `TRUNCATED`
- `PENDING`
- `FAILED`
- `UNKNOWN`
- `INVALID_SOURCE`

State transitions must be driven only by validated snapshot metadata. UI state must not trigger runtime actions.

## Requirements
- Preserve exact source status and provenance.
- Do not infer PASS from absence of FAIL.
- Do not infer RUNNING from timestamps alone.
- Do not infer owner from executable/file names.
- Preserve conflict/malformed evidence as `INVALID_SOURCE` or `UNKNOWN` according to the canonical contract.
- Keep state serialization deterministic.
- Bound error/source messages.

## Safety
No execution, authorization, approval, persistence, network, tool/MCP/browser/Computer Use, shell, workflow, build/install/release, or OS-input behavior.

## Tests / evidence
Test every state, legal/illegal transitions, malformed source, owner mismatch, conflicting evidence, truncation, deterministic serialization, and source immutability. Produce clean `.diff` and machine-readable evidence artifacts.

## Workflow discipline
No manual workflow dispatch and no automatic merge.