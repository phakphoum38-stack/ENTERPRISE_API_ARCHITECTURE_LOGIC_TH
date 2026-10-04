# Tool Registry

Baseline: `main` @ `a06f0b7`

Lifecycle values: `active` is used by current workflows; `compatibility` is retained for V1/V2; `verify` requires deployment or platform evidence; `documentation` is a contract/tool definition without a standalone runtime.

| Tool family | Canonical entry points | Owner | Input / output contract | Runtime dependency | Authentication / secrets | Evidence | Lifecycle |
|---|---|---|---|---|---|---|---|
| Research OS API | `tools/research_os_api/server.py`, `openapi.yaml` | Research OS API | HTTP JSON API; OpenAPI contract; JSON responses and status codes | Python 3.12; optional Friend service; provider integrations | Session, sync key, OAuth and provider secrets as documented in auth audit | `tools/research_os_api/test_*.py`; 114 tests passed | active |
| Research Curator / Knowledge | `tools/research_curator/curator.py`, `knowledge_ops.py`, `workspace_engine.py` | Research OS knowledge | Conversation/artifact input; artifact, diff and graph output | Python; filesystem under `research/` | Local filesystem boundary; no provider secret required for core operations | curator and knowledge/workspace tests | active |
| House Command | `tools/house_command/dispatcher.py`, `house_brain.py` | House / Research OS | Command request; house status, health and next-focus payload | Python; GitHub dispatch/API for remote use | GitHub token only for API-triggered operations | `tools/house_command/test_house_brain.py` | active |
| V3 runtime smoke/evidence | `v3/scripts/smoke.py`, `service_smoke.py`, `storage_smoke.py`, `evidence.py` | V3 runtime | Smoke command; JSON evidence artifact | Python 3.12; local runtime/storage | Local runtime boundary; provider smoke may require provider configuration | V3 test suite; worker recovery evidence | active |
| V3 factory/provider validation | `v3/scripts/factory_execution_smoke.py`, `provider_smoke.py`, `provider_resilience_smoke.py` | V3 release validation | Stage/provider input; evidence JSON and exit status | Python; configured provider for live probes | Provider credentials only for live provider probes | V3 factory/provider workflows | verify |
| File audit | `tools/file_audit_v6x6.py`, `tools/test_file_audit_v6x6.py` | Repository governance | Repository path/config; audit report and exit status | Python; optional PowerShell wrapper | No runtime secret required | file-audit tests and workflow | active |
| Owner Friend / ServiceHost | `owner_special/scripts/run_friend_service.py`, `build_bundle.py`, `tools/research_os_service/` | Owner Special | Service/chat requests; bundle, installer and service artifacts | Python; .NET/Windows for ServiceHost; Flutter for desktop | Owner/profile headers; packaging credentials must remain external | owner-special tests, smoke and Windows workflows | verify |
| Windows lifecycle scripts | `scripts/start-research-os-local.ps1`, `stop-*`, `status-*`, `setup-*` | Research OS Windows | Local service lifecycle; process/status output | Windows PowerShell and installed service | Local machine/service permissions | Windows artifact and E2E workflows | verify |
| Flutter canonical toolset | `tools/flutter_canonical/` | Flutter/toolchain governance | Asset/tool validation inputs; validation result | Flutter/Dart and platform SDKs | No server secrets in client bundle | GUI asset workflows and Flutter tests | verify |
| Generate contract tools | `current/tools/generate-*.md`, `current/GENERATE_*.md` | Generate Orchestrator | Versioned contract/document inputs; generated workflow artifacts | Repository tooling and CI | GitHub workflow permissions as applicable | generate orchestrator validation workflows | documentation |
| Workflow runtime contracts | `current/workflow-runtime/*.yml` | Workflow Runtime | Workflow, state, event and retry contract documents | Provider-neutral; implementation owned by runtime | Contract does not define credentials | Contract validation and V3 runtime tests | active |

## Registry rules

- A tool is canonical only when its entry point, owner, input/output boundary and evidence are named.
- Tool registry status does not imply production readiness; `verify` remains open until platform/deployment evidence exists.
- V1/V2 compatibility tools must not be retired without a replacement, migration path, tests and release evidence.
- Secrets are referenced by variable/header name only; secret values never belong in this registry.

## Open follow-up

- Add direct command examples for each family where the interface is stable.
- Attach exact workflow run URLs or evidence artifact identifiers during release certification.
- Split compatibility and retirement decisions into the V1/V2 compatibility map.
