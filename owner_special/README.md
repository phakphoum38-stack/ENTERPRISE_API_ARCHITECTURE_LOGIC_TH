# Research OS — Owner Special / Friend Complete V1.2

This directory is the owner edition of Research OS and is intentionally separated from the standard V3 release line.

## Friend Complete architecture

The owner edition keeps the Friend architecture in our own files:

- owner identity and owner-only authorization boundary
- Brain Core with adaptive 1^3 / 3^3 / 6^3 / 6^6 logical capacity
- high-level planning and reasoning summaries
- skill catalog and registry
- owner/profile/session scoped memory with atomic disk persistence
- scoped context assembly and policy/tool permissions
- provider adapters and routing
- V3 bridge to BrainCore, UnifiedMasterOrchestrator, SoftwareFactory, FactoryExecutionEngine, ProviderRegistry and UserDataLayout
- capability registry describing every Friend layer
- loopback-only Owner Friend Service
- Owner Desktop Flutter shell consuming the Friend Service contract
- startup probe proving `/owner/health` and `/owner/status`
- credential-redacted evidence and HTTP path/status audit
- portable Owner Bundle builder
- Windows + Ubuntu Python validation and Windows Desktop E2E

The owner files contain the orchestration, behavior contracts, skills, context, memory boundaries, tools, integration, evidence and portability layers. Model intelligence remains behind provider adapters.

## Service contract

The Owner Friend Service binds only to `127.0.0.1` and exposes:

```text
GET  /owner/health
GET  /owner/status
GET  /owner/memory
POST /owner/chat
```

Authenticated endpoints require `X-Research-OS-Owner`; profile and session are carried by `X-Research-OS-Profile` and `X-Research-OS-Session`. The owner boundary is checked before memory, skills, tools or providers run.

A chat response contains the Friend decision scale/capacity and the V3 Software Factory stage plan:

```text
master → factory → team → tests → release
```

## Persistent owner data

With `data_root` enabled, data stays outside the portable source bundle:

```text
<data_root>/owners/<owner-id>/memory/memory.json
<data_root>/owners/<owner-id>/evidence/events.jsonl
```

## Desktop

The separate Owner Desktop lives at `owner_special/flutter_app`. At startup it probes the Friend Service and then provides Friend, Capabilities and Memory views from the same owner-scoped runtime.

Runtime configuration uses environment variables:

```text
RESEARCH_OS_OWNER_ID
RESEARCH_OS_OWNER_PROFILE
RESEARCH_OS_OWNER_SESSION
RESEARCH_OS_FRIEND_URL
RESEARCH_OS_OWNER_DATA_ROOT
```

## Run locally

```bash
PYTHONPATH=owner_special python -m unittest discover -s owner_special/tests -p "test_*.py" -v
PYTHONPATH=owner_special python owner_special/scripts/smoke.py
PYTHONPATH=owner_special python owner_special/scripts/run_friend_service.py --owner-id owner
PYTHONPATH=owner_special python owner_special/scripts/build_bundle.py
```

For the Desktop, run `flutter create . --platforms=windows` once inside `owner_special/flutter_app`, then `flutter pub get`, `flutter test`, and `flutter run -d windows`.

## Release rule

Owner Special remains a separate release line. Do not merge it into standard V3 merely to ship the normal application. Promote it only after its own Python, Desktop E2E and Owner Bundle certification are green and the owner explicitly chooses to publish or merge it.
