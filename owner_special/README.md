# Research OS — Owner Special / Friend Complete V1

This directory is the private-owner edition of Research OS. It is intentionally separated from the standard V3 release line.

## What “Friend Complete” means

The owner edition carries an explicit software architecture for the assistant/friend layer:

- owner identity and owner-only boundary
- Brain Core with adaptive 1^3 / 3^3 / 6^3 / 6^6 capacity selection
- high-level planning/reasoning summaries
- skills catalog and skill registry
- scoped memory and context
- tool registry and permission checks
- provider adapters and routing
- orchestrator/composition root
- evidence/audit with credential redaction
- runtime entry point
- tests and smoke validation

It does **not** copy proprietary model weights, hidden chain-of-thought, or private internals from any hosted AI model. Model intelligence remains behind provider adapters. The local Friend architecture owns orchestration, skills, context, memory boundaries, tools, evidence, and behavior contracts.

## Layout

```text
owner_special/
├─ OWNER_MANIFEST.json
├─ research_os_friend/
│  ├─ identity.py
│  ├─ models.py
│  ├─ brain.py
│  ├─ reasoning.py
│  ├─ skills.py
│  ├─ memory.py
│  ├─ context.py
│  ├─ policy.py
│  ├─ tools.py
│  ├─ providers.py
│  ├─ evidence.py
│  ├─ catalog.py
│  ├─ orchestrator.py
│  └─ runtime.py
├─ scripts/smoke.py
└─ tests/test_friend_complete.py
```

## Owner boundary

`FriendRuntime` is created for one `owner_id`. Requests from a different owner ID are rejected before skills, tools, memory, or providers can run. Memory is additionally scoped by profile and session.

## Reasoning boundary

The reasoning module stores only a concise decision summary, selected capabilities, plan steps, evidence references, and outcomes. It intentionally does not persist hidden token-by-token reasoning.

## Run locally

```bash
PYTHONPATH=owner_special python -m unittest discover -s owner_special/tests -p "test_*.py"
PYTHONPATH=owner_special python owner_special/scripts/smoke.py
```

## Release rule

Owner Special is a separate release line. Do not merge it into the standard V3 branch merely to ship the normal application. Promote it only after its own CI is green and the owner explicitly chooses to publish or merge it.
