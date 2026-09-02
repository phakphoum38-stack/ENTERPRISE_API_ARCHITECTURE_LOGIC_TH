# Research OS Multi-Login Architecture

Research OS is the identity and session boundary. Login providers authenticate the user; Research OS converts the result into one provider-neutral principal and one Research OS session.

## Providers

Initial providers:

- Google OAuth / OpenID Connect
- Microsoft identity platform
- GitHub OAuth

The provider registry exposes only public configuration metadata. Client secrets and provider tokens must remain server-side and must never be passed through Friend prompts or Calendar Tool arguments.

## Runtime boundary

```text
Login Provider
      |
      v
Research OS Auth Gateway
      |
      v
Unified Principal + Research OS Session
      |
      +--> Friend AI
      +--> Google Workspace tools
      +--> Calendar Tool (optional)
```

`phakphum-calendar` is an optional tool/engine. Research OS login must not require it to be installed, running, or authenticated.

## Session identity

Provider-specific subjects are normalized to a common principal shape:

```json
{
  "provider": "google",
  "sub": "provider-subject",
  "email": "user@example.com",
  "name": "User",
  "picture": "..."
}
```

The existing signed Research OS session remains the application session boundary. Provider access tokens are not part of the Friend tool contract.

## Security requirements

1. Use short-lived, single-use OAuth state values for callbacks.
2. Validate the redirect URI against configured values.
3. Keep client secrets and refresh tokens on the server side.
4. Request least-privilege scopes; identity login should not implicitly grant Calendar, Drive, or Gmail access.
5. Do not log authorization codes, access tokens, refresh tokens, or client secrets.
6. Resolve tool authorization from the verified Research OS session, not a user-supplied identity field.
7. Calendar remains optional and must fail closed when unavailable without preventing Research OS startup.

## Implementation stages

1. Provider registry and normalized principal — implemented.
2. Multi-provider OAuth start/callback routing and session issuance — next.
3. Login UI with provider availability — next.
4. Account linking and provider unlinking — after the first end-to-end provider flows.
5. Optional tool authorization using the unified session.
