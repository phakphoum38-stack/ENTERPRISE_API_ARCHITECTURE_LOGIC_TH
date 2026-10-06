# Research OS Google OIDC Production Binding

## Protocol

Research OS Google sign-in uses the Google OAuth 2.0 Authorization Code flow with OpenID Connect identity scopes:

- `openid`
- `email`
- `profile`

Google is the identity provider. Research OS remains the identity/session and authorization boundary.

## Production configuration

The production API must receive these server-only variables:

- `RESEARCH_OS_GOOGLE_CLIENT_ID`
- `RESEARCH_OS_GOOGLE_CLIENT_SECRET`
- `RESEARCH_OS_GOOGLE_IDENTITY_REDIRECT_URI`

The production redirect URI is:

`https://research-os-api-phakphoum.onrender.com/v1/auth/google/callback`

The client secret must be configured only in the production deployment secret store. It must never be committed to Git, embedded in Flutter/web assets, or supplied through ordinary client requests.

## Flow

```text
Research OS client
    -> /v1/auth/google/start
    -> Google Authorization Server
    -> /v1/auth/google/callback
    -> validate OAuth state
    -> exchange authorization code server-side
    -> resolve Google identity
    -> issue signed Research OS session
    -> /v1/auth/status
```

For native clients, the OAuth state may also be used as the short-lived single-use backend handoff key. The Research OS session itself must not appear in the OAuth callback URL.

## Boundaries

- Google identity is separate from Google Workspace authorization.
- Workspace scopes must not be requested merely to sign in.
- Client code cannot grant or override Research OS roles.
- Invalid, missing, or expired authentication state fails closed.
- Production readiness requires deployment evidence in addition to unit tests.

## Release evidence

Production is not considered ready until all of the following are proven:

1. Google OAuth client is the dedicated Research OS production client.
2. Redirect URI exactly matches the production callback.
3. Server-only credentials are configured in Render production.
4. Google login completes and creates a valid Research OS session.
5. `/v1/auth/status` reports the server-derived identity.
6. Invalid/expired state and invalid authorization codes fail closed.
7. Logs and client bundles contain no OAuth client secret or session credential.
8. The exact deployed commit is recorded with the authentication test evidence.
