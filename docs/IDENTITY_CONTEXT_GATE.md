# Research OS Identity Context Gate

## Purpose

Keep Friend bound to the verified Research OS principal and the correct workspace/profile/session. The shared Flutter UI must not choose a user identity by prompt or by an untrusted client-supplied owner field.

## Verified current path

```text
Google / Research OS login
        -> signed Research OS session
        -> /v1/ai/generate
        -> Friend proxy
        -> Owner Friend Service :8790
        -> owner/profile/session scoped memory
```

The signed session contains `user_id`, `email`, `role`, `session_id`, `iat`, and `exp`. `verify_session()` validates the signature, expiry, completeness, and revocation state.

The Owner Friend Service already validates `X-Research-OS-Owner`, `X-Research-OS-Profile`, and `X-Research-OS-Session` before protected operations and passes those scopes into Friend requests and memory recall.

## Current gap

The canonical `/v1/ai/generate` Friend route currently forwards only the request body's `session_id` to the Friend proxy and uses the server's configured Friend owner/profile values. It does not yet derive the Friend owner/profile context from the verified Research OS session.

That means the identity boundary is stronger inside the Owner Friend Service than at the canonical API-to-Friend handoff. This must be closed before treating multi-user Friend isolation as complete.

## Required invariant

> Friend must be placed with the correct person, system/workspace, and data.

For the shared Research OS UI, the canonical flow must be:

```text
Verified Research OS session
        |
        +--> principal.user_id
        +--> principal.role
        +--> session_id
        |
        v
Trusted identity context
        |
        +--> Friend owner/workspace/profile binding
        +--> Memory scope
        +--> Knowledge scope
        +--> Tool authorization
```

A client-supplied identity field must never override the verified session principal.

## Acceptance criteria

1. Friend requests with no valid Research OS session are rejected when the Friend route requires identity.
2. A valid session determines the effective user context server-side.
3. Client-supplied owner/profile/session identity cannot cross the verified session boundary.
4. Memory recall and writes use the same effective identity context as Friend.
5. Different users cannot read or write another user's Friend memory/workspace through the canonical API.
6. Existing Owner Special loopback protection remains intact.
7. Existing app branding remains canonical: `apps/research_os_flutter/assets/branding/research_os_master.webp` -> Windows `runner/resources/app_icon.ico`.
8. Flutter, Windows EXE identity, installer, and E2E gates remain green after the change.
