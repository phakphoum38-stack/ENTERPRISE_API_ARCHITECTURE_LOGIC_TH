# Research OS Multi-Login Identity Gateway

Research OS is the identity and session boundary. `phakphum-calendar` remains an optional Calendar Tool and is never a prerequisite for Research OS login.

## Providers

The first provider set is:

- Google
- Microsoft
- GitHub

The registry is provider-neutral so additional OIDC/OAuth providers can be added without changing Friend or Calendar Tool contracts.

## Identity flow

```text
Provider OAuth/OIDC
        |
        v
Research OS Identity Gateway
        |
        v
Unified Research OS Principal
        |
        v
Signed Research OS Session
        |
   +----+---------+---------+
   |              |         |
 Friend        Workspace  Tools
                           |
                    phakphum-calendar
```

Provider credentials are server-side configuration. OAuth access/refresh tokens must never be accepted through Friend prompts, Calendar Tool arguments, or ordinary client payloads.

## Provider configuration

Google uses the existing `RESEARCH_OS_GOOGLE_CLIENT_ID` and `RESEARCH_OS_GOOGLE_CLIENT_SECRET` configuration.

Microsoft:

- `RESEARCH_OS_MICROSOFT_CLIENT_ID`
- `RESEARCH_OS_MICROSOFT_CLIENT_SECRET`
- optional `RESEARCH_OS_LOGIN_MICROSOFT_ENABLED=false`

GitHub:

- `RESEARCH_OS_GITHUB_CLIENT_ID`
- `RESEARCH_OS_GITHUB_CLIENT_SECRET`
- optional `RESEARCH_OS_LOGIN_GITHUB_ENABLED=false`

A provider is advertised as available only when it is enabled and both client credentials are configured.

## Account linking

The normalized principal shape is provider-neutral (`sub`, `email`, `name`, optional profile fields). Account linking must be an explicit authenticated action; matching email addresses alone must not silently merge two provider identities.

## Calendar boundary

`phakphum-calendar` is an optional tool. Research OS login works independently of it. Calendar operations receive authenticated Research OS context and tool commands, not OAuth secrets.
