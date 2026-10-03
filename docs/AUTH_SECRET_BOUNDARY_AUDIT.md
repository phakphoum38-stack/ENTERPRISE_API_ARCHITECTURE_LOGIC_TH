# Authentication and Secret Boundary Audit

Baseline: `main` @ `a06f0b7`

## Verified boundaries

| Boundary | Source | Evidence | Status |
|---|---|---|---|
| Research OS user session | `tools/research_os_api/api_auth.py` | `test_v2_server.py`, `test_agent_server.py` | verified |
| Cloud conversation access | `server.py` requires verified session and sync key | API suite covers 401 and successful scoped operations | verified |
| Memory commit capability | `server.py` requires `X-Research-OS-Sync-Key` | `test_api.py` | verified |
| Google identity OAuth | `google_identity.py` | `test_google_identity.py` verifies identity-only scopes | verified |
| Google Workspace OAuth | `google_oauth.py` | `test_google_oauth.py` verifies configuration and secret redaction | verified |
| Provider credentials | provider readiness and adapters | `test_provider_readiness.py` | verified |
| Developer identity proxy | `developer_identity.py` and developer server | `test_developer_identity.py`, `test_developer_server.py` | verified |
| Readiness/observability output | V2 observability redaction | `test_v2_observability.py` | verified |

## Required secrets and ownership

| Variable/header | Boundary | Client exposure |
|---|---|---|
| `RESEARCH_OS_SESSION_SECRET` | Server session signing/verification | server only |
| `RESEARCH_OS_IDENTITY_PROXY_SECRET` | Developer identity gateway | gateway/server only |
| `RESEARCH_OS_SYNC_KEY` / `X-Research-OS-Sync-Key` | Protected cloud sync and memory commit | server or trusted operator only |
| `RESEARCH_OS_GOOGLE_CLIENT_SECRET` | Google OAuth token exchange | server only |
| Provider API keys | Provider adapter calls | server only |
| `X-Research-OS-Session` or session cookie | Verified user session credential | client may hold credential; never log |

## Findings

- Existing tests demonstrate fail-closed behavior for missing/invalid sessions and sync keys.
- Google identity scopes are separated from Google Workspace scopes.
- OAuth authorization URLs do not include client secrets.
- Runtime logs and readiness responses have redaction coverage for nested secret values.
- Production deployment evidence is still required: secret source configuration, rotation procedure, log review, TLS termination, and confirmation that client bundles do not contain server-only variables.
- This audit does not authorize exposing `RESEARCH_OS_SYNC_KEY`, OAuth client secrets, provider keys, or identity proxy secrets to Flutter/web clients.

## Release checklist

- [ ] Configure server-only variables in the deployment secret store.
- [ ] Confirm production URLs and Google redirect URIs match the registered OAuth clients.
- [ ] Verify TLS and secure cookie settings at the public edge.
- [ ] Verify production logs contain no credentials or session tokens.
- [ ] Document rotation and revocation ownership.
- [ ] Attach exact-SHA deployment evidence to the release gate.
