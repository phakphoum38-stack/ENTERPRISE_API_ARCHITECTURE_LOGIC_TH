# Launch Desk Agent

Issue #213 adds Launch Desk to the existing Owner Friend service and desktop workspace.

## Flow

`Flutter Launch Desk -> Friend Service -> OpenAI Agents SDK -> OpenAI Responses API`

The service exposes `POST /v1/launch-desk/run` as an authenticated loopback-only SSE endpoint. Each event is JSON on an SSE `data:` line.

Event types:

- `started` — run accepted
- `plan_ready` — deterministic readiness contract is available
- `tool_event` — Agents SDK function tool called/output
- `model_text_delta` — streamed model text delta
- `final` — final model text plus the deterministic plan

## Deterministic tools

The agent is required to use:

1. `extract_tasks`
2. `check_launch_readiness`
3. `generate_owner_checklist`
4. `draft_launch_copy`

Readiness is evaluated across product, engineering, QA, infrastructure, security, docs, support/comms, rollback, and monitoring/observability. Missing evidence is treated as `needs-attention`; it is never invented as confirmed evidence.

## Credential boundary

Launch Desk reuses the existing Owner Provider credential through `ProviderManager`. The secret remains in the configured secure backend and is passed only in-process to the Agents SDK provider adapter. It is not returned by an HTTP response or desktop status API. Agents SDK tracing is disabled for this local credential path so the provider key is not exported through tracing.

## Local real smoke

After the Owner Friend service is running and the Provider page reports a connected provider, run a real Launch Desk request from the Owner Desktop and confirm the activity stream shows tool events followed by model deltas and a final event. The deterministic plan should always contain nine readiness areas.

CI runs the deterministic contract and package/compile validation. A live OpenAI smoke should use the already configured local Owner credential rather than adding a duplicate repository secret.
