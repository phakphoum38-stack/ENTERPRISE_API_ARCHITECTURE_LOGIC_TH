# Research OS Owner Authorization

## Authority boundary

Research OS separates authenticated identity from authorization. A verified
Research OS session is the only source of principal identity for protected API
actions. Client request fields must not be trusted to select a user or role.

The system-level `OWNER` role is unrestricted by resource or scope. Resource
ownership in file ACLs is a separate concept and must not escalate into the
system Owner role.

## Workflow controls

The following orchestration actions require a verified Owner session:

- `POST /v1/agents/orchestrations/{run_id}/execute`
- `POST /v1/agents/orchestrations/{run_id}/confirm`
- `POST /v1/agents/orchestrations/{run_id}/retry`
- `POST /v1/agents/orchestrations/{run_id}/cancel`

Unauthenticated requests fail closed with `401`. Authenticated non-Owner
requests receive `403`.

Creating and observing an orchestration remain separate from these control
actions. The UI may expose controls only as a representation of server
authority; rendering a button never grants authority.

## Owner identity mapping

At login completion, the backend derives the principal from the verified
identity-provider profile and assigns:

- `OWNER` when the verified user ID is listed in
  `RESEARCH_OS_CODE_OWNER_IDS`, or the verified email is listed in
  `RESEARCH_OS_OWNER_EMAILS`.
- `USER` otherwise.

These are server-side configuration values. They are never accepted from
request JSON, query parameters, or Flutter UI state.

## Recovery boundary

Retry and cancellation operate through the existing orchestration lifecycle.
They must not create a second queue, worker pool, or DLQ implementation.

Resource-conflict handling remains governed by Resource Lineage: a stale
version is rejected, execution stops, resources are released, and delivery is
acknowledged/reconciled according to policy. No conflicting version is
overwritten.

## Evidence

Authorization decisions should remain attributable to the verified principal
and the canonical workflow/run identity so the Final Gate can verify the same
lineage before release.

## Developer identity gateway

The separate Developer Platform accepts only short-lived signed identity
assertions. The canonical Research OS API provides the trusted bridge:

```text
Research OS OAuth
      -> verified Research OS session
      -> POST /v1/auth/developer/assertion
      -> server derives user_id/email/role from the verified session
      -> short-lived HMAC assertion
      -> Developer Platform
      -> Owner/grant authorization
```

The endpoint accepts the canonical Research OS session through
`X-Research-OS-Session` (or the existing authenticated session cookie). It
never accepts a client-supplied principal, user ID, or role for the assertion.

`RESEARCH_OS_IDENTITY_PROXY_SECRET` remains server-only. The Flutter client
must never contain this secret or implement HMAC signing itself.

Assertions are bounded by `RESEARCH_OS_IDENTITY_ASSERTION_MAX_AGE` and are
verified by the Developer Platform's existing nonce-replay protection. Missing
or invalid Research OS sessions fail closed with `401`; a missing gateway
signing secret fails closed with `503`.

The gateway is an authentication bridge, not an authorization bypass.
Developer grants, Owner authorization, resource ownership, and the original
SHA/version checks remain enforced by the Developer Platform.
