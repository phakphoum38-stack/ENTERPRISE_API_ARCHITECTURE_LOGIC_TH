# Research OS API Implementation Matrix

Baseline: `main` @ `a06f0b7`

This matrix compares the OpenAPI contract at `tools/research_os_api/openapi.yaml` with the dependency-free implementation in `tools/research_os_api/server.py` and the existing API tests.

## Contracted paths

| Path group | OpenAPI | Implementation | Evidence | Status |
|---|---|---|---|---|
| `/health` | GET | `server.py` GET | `test_api.py`, `test_e2e.py` | verified |
| `/v1/providers` | GET | `server.py` GET | `test_api.py`, `test_v2_openapi.py` | verified |
| `/v1/ai/generate` | POST | `server.py` POST | `test_api.py`, `test_e2e.py` | verified |
| `/v1/conversations/analyze` | POST | `server.py` POST | `test_api.py`, `test_e2e.py` | verified |
| `/v1/knowledge/artifacts`, `/v1/knowledge/graph` | GET | `server.py` GET | `test_api.py` | verified |
| `/v1/agents`, `/v1/agents/readiness`, `/v1/agents/discover` | GET | `server.py` GET | `test_agent_server.py`, `test_v2_openapi.py` | verified |
| `/v1/agents/orchestrations` | GET, POST | `server.py` GET/POST | `test_agent_server.py`, `test_agent_orchestrator_persistence.py` | verified |
| `/v1/agents/orchestrations/{run_id}` | GET | `server.py` GET | `test_agent_server.py` | verified |
| `/v1/agents/orchestrations/{run_id}/timeline` | GET | `server.py` GET | `test_agent_server.py` | verified |
| `/v1/agents/orchestrations/{run_id}/execute` | POST | `server.py` POST | `test_agent_server.py`, `test_v2_openapi.py` | verified |
| `/v1/agents/orchestrations/{run_id}/confirm` | POST | `server.py` POST | `test_agent_server.py`, `test_v2_openapi.py` | verified |
| `/v1/agents/orchestrations/{run_id}/retry` | POST | `server.py` POST | `test_agent_server.py`, `test_v2_openapi.py` | verified |
| `/v1/agents/orchestrations/{run_id}/cancel` | POST | `server.py` POST | `test_agent_server.py`, `test_v2_openapi.py` | verified |
| `/v2/health/readiness` | GET | `server.py` GET | `test_v2_server.py`, `test_v2_openapi.py` | verified |
| `/v2/agents`, `/v2/agents/readiness`, `/v2/agents/discover` | GET | `server.py` GET | `test_v2_server.py`, `test_v2_openapi.py` | verified |
| `/v2/orchestrations` | GET, POST | `server.py` GET/POST | `test_v2_server.py`, `test_v2_openapi.py` | verified |
| `/v2/orchestrations/{run_id}` | GET | `server.py` GET | `test_v2_server.py`, `test_v2_openapi.py` | verified |
| `/v2/orchestrations/{run_id}/timeline` | GET | `server.py` GET | `test_v2_server.py`, `test_v2_openapi.py` | verified |
| `/v2/orchestrations/{run_id}/execute` | POST | `server.py` POST | `test_v2_server.py`, `test_v2_openapi.py` | verified |
| `/v2/orchestrations/{run_id}/confirm` | POST | `server.py` POST | `test_v2_openapi.py` | verified |
| `/v2/orchestrations/{run_id}/retry` | POST | `server.py` POST | `test_v2_openapi.py` | verified |
| `/v2/orchestrations/{run_id}/cancel` | POST | `server.py` POST | `test_v2_openapi.py` | verified |
| `/v2/workspaces` | GET | `server.py` GET | `test_v2_server.py`, `test_v2_openapi.py` | verified |
| `/v2/workspaces/{workspace_id}/knowledge` | GET | `server.py` GET | `test_v2_server.py`, `test_v2_openapi.py` | verified |

## Implemented paths added to OpenAPI

These routes are implemented, tested, and now declared in `openapi.yaml`. They remain draft/public-promotion candidates until deployment and authentication evidence is complete.

| Path group | Methods | Evidence | Status |
|---|---|---|---|
| `/v1/auth/google/{start,status,callback,signout}` | GET/POST | `test_google_identity.py`, `test_google_oauth.py` | declared; pending release evidence |
| `/v1/google-workspace/{dashboard,services}` | GET/POST | `test_google_workspace.py` | declared; pending release evidence |
| `/v1/google-workspace/oauth/{start,status,callback,disconnect}` | GET/POST | `test_google_oauth.py`, `test_google_workspace.py` | declared; pending release evidence |
| `/v1/conversations/cloud` | GET | `test_conversation_store.py`, `test_e2e.py` | declared; pending release evidence |
| `/v1/conversations/cloud/{sync,delete}` | POST | `test_conversation_store.py`, `test_e2e.py` | declared; pending release evidence |
| `/v1/memory/search` | GET | `test_api.py` | declared; pending release evidence |
| `/v1/memory/commit` | POST | `test_api.py` | declared; pending release evidence |
| `/v1/ai/answer-with-memory` | POST | `test_api.py` | declared; pending release evidence |
| `/v1/github/dashboard` | GET | `test_e2e.py` | declared; pending release evidence |

## Scope and release decision

- OpenAPI contract coverage is strong for the V1/V2 agent, orchestration, readiness, and workspace surfaces.
- The newly added Google identity, Google Workspace, cloud conversations, memory, and GitHub dashboard routes are declared with draft-level schemas.
- Cloud conversation operations now declare the required `X-Research-OS-Session` and `X-Research-OS-Sync-Key` headers; memory commit declares the sync key requirement.
- No endpoint is marked production-ready solely from unit tests. Public promotion still requires auth behavior, deployment evidence, and exact-SHA release-gate evidence.
- V2 remains compatibility/runtime surface until a versioned V3 API contract supersedes it.

## Next action

Add schema-level response and authentication requirements, then collect deployment evidence before changing the OpenAPI version/status metadata.
