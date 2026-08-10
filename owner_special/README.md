# Research OS — Owner Special / Friend Complete V1

This directory is the owner edition of Research OS and is intentionally separated from the standard V3 release line.

## Friend Complete architecture

The owner edition keeps the Friend architecture in our own files:

- owner identity and owner-only authorization boundary
- Brain Core with adaptive 1^3 / 3^3 / 6^3 / 6^6 logical capacity
- high-level planning and reasoning summaries
- skill catalog and registry
- owner/profile/session scoped memory
- atomic persistent owner memory
- scoped context assembly
- policy and tool permissions
- tool registry
- provider adapters and routing
- V3 bridge to BrainCore, UnifiedMasterOrchestrator, SoftwareFactory, FactoryExecutionEngine, ProviderRegistry and UserDataLayout
- capability registry describing every Friend layer
- credential-redacted evidence and audit
- runtime composition root
- portable Owner Bundle builder
- cross-platform tests and smoke validation

It does **not** copy proprietary model weights, hidden chain-of-thought, or private internals from hosted AI models. Model intelligence remains behind provider adapters. The files in this edition own orchestration, behavior contracts, skills, context, memory boundaries, tools, integration, evidence and portability.

## Layout

```text
owner_special/
├─ OWNER_MANIFEST.json
├─ README.md
├─ pyproject.toml
├─ research_os_friend/
│  ├─ identity.py
│  ├─ models.py
│  ├─ brain.py
│  ├─ reasoning.py
│  ├─ skills.py
│  ├─ memory.py
│  ├─ persistent_memory.py
│  ├─ context.py
│  ├─ policy.py
│  ├─ tools.py
│  ├─ providers.py
│  ├─ capabilities.py
│  ├─ v3_bridge.py
│  ├─ evidence.py
│  ├─ catalog.py
│  ├─ orchestrator.py
│  ├─ bundle.py
│  └─ runtime.py
├─ scripts/
│  ├─ smoke.py
│  └─ build_bundle.py
└─ tests/
   ├─ test_friend_complete.py
   └─ test_friend_persistence.py
```

## Owner boundary and persistence

`FriendRuntime` is created for one `owner_id`. Requests from another owner ID are rejected before skills, tools, memory, or providers can run. With `data_root` enabled, memory is stored under:

```text
<data_root>/owners/<owner-id>/memory/memory.json
<data_root>/owners/<owner-id>/evidence/events.jsonl
```

Memory reads remain scoped to owner/profile/session. Writes use an atomic replace so a completed memory update becomes one complete file version.

## V3 bridge

`V3Bridge` discovers the Research OS V3 owned core and verifies the exports required by Friend Complete. The bridge does not copy the V3 implementation; it connects the owner edition to the same Brain, Factory, Provider and user-data contracts already certified in V3 Clean.

## Reasoning boundary

The reasoning module stores only a concise decision summary, selected capabilities, plan steps, evidence references and outcomes. It intentionally does not persist hidden token-by-token reasoning.

## Owner Bundle

The CI build creates `Research-OS-Owner-Special-Friend-Complete.zip`. It contains the owner architecture source, tests and manifests. Runtime owner data is not included in the portable source bundle.

## Run locally

```bash
PYTHONPATH=owner_special python -m unittest discover -s owner_special/tests -p "test_*.py" -v
PYTHONPATH=owner_special python owner_special/scripts/smoke.py
PYTHONPATH=owner_special python owner_special/scripts/build_bundle.py
```

## Release rule

Owner Special remains a separate release line. Do not merge it into standard V3 merely to ship the normal application. Promote it only after its own CI is green and the owner explicitly chooses to publish or merge it.
