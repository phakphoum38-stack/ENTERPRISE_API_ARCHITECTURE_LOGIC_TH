# Research OS Flutter — Current Module Inventory

Frozen for new GUI work.

## Source composition

- `lib/src/app_shell.dart`
- `lib/src/research_os_app.dart`
- `lib/src/api/`
- `lib/src/features/`
- `lib/src/platform/`
- `lib/src/ui/`

## Existing feature modules confirmed

- `features/home`
- `features/chat`
- `features/agents`
- `features/checkin`
- `features/library`
- `features/graph`
- `features/github`
- `features/google_workspace`
- `features/local_api`
- `features/monitor`
- `features/settings`
- `features/developer_access`

## Existing desktop navigation destinations

| Index | Section | Destination |
|---:|---|---|
| 0 | Workspace | Home |
| 1 | Workspace | AI Chat |
| 2 | Workspace | Agent Center |
| 11 | Workspace | Check-in |
| 3 | Knowledge | Library |
| 4 | Knowledge | Knowledge Graph |
| 5 | Connections | GitHub |
| 6 | Connections | Google Workspace |
| 7 | System | Local API & Service |
| 8 | System | System Monitor |
| 9 | System | Settings |
| 10 | Access | Developer Access |

## API endpoints consumed by the current Flutter client

### Core / Health

- `GET /health`
- `GET /v1/providers`

### Knowledge

- `GET /v1/knowledge/artifacts`
- `GET /v1/knowledge/graph`
- `GET /v2/workspaces`
- `GET /v2/workspaces/{workspaceId}/knowledge`

### Google identity / Workspace

- `GET /v1/auth/google/status`
- `POST /v1/auth/google/start`
- `POST /v1/auth/google/signout`
- `GET /v1/google-workspace/dashboard`
- `GET /v1/google-workspace/oauth/status`
- `POST /v1/google-workspace/oauth/start`
- `POST /v1/google-workspace/oauth/disconnect`
- `POST /v1/google-workspace/services`

### Agents / Orchestration

- `GET /v1/agents`
- `GET /v1/agents/readiness`
- `GET /v1/agents/discover`
- `GET /v1/agents/orchestrations`
- `GET /v1/agents/orchestrations/{runId}`
- `GET /v1/agents/orchestrations/{runId}/timeline`
- `POST /v1/agents/orchestrations`
- `POST /v1/agents/orchestrations/{runId}/execute`
- `POST /v1/agents/orchestrations/{runId}/confirm`
- `POST /v1/agents/orchestrations/{runId}/retry`
- `POST /v1/agents/orchestrations/{runId}/cancel`

### GitHub

- `GET /v1/github/dashboard`

### Memory / AI / Chat

- `GET /v1/memory/search`
- `POST /v1/ai/generate`
- `POST /v1/ai/answer-with-memory`
- `POST /v1/memory/commit`
- `GET /v1/conversations/cloud`
- `POST /v1/conversations/cloud/sync`
- `POST /v1/conversations/cloud/delete`

## Current Chat path

`ChatPage._send()` -> builds the latest prompt plus up to 10 prior messages -> `ResearchOSApiClient.answerWithMemory(...)` -> `POST /v1/ai/answer-with-memory`.

The client sends JSON with `question` and optional `provider`.

## Current Chat empty state

Current title: `มีอะไรให้ช่วย?`

Requested new title: `สวัสดีเริ่มทำอะไรดี`

This change is approved for the new GUI workstream but should be accompanied by widget regression coverage.

## Current Flutter dependencies

- Flutter SDK
- `flutter_markdown`
- `http`
- `shared_preferences`
- `url_launcher`

The current pubspec does not yet include a launcher-icon generation package or declared image assets.

## Existing tests confirmed

- `agent_center_test.dart`
- `api_client_provider_routing_test.dart`
- `chat_flow_test.dart`
- `check_in_page_test.dart`
- `desktop_shell_test.dart`
- `developer_access_page_test.dart`
- `enterprise_components_responsive_test.dart`
- `system_monitor_test.dart`
- `widget_test.dart`

## Freeze rule

Before a feature module is removed, replaced, renamed, or its endpoint contract is changed, the new implementation must prove equivalent or improved behavior with tests/evidence. New GUI work should prefer adapters and shell composition over rewrites.
