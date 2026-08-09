# Research OS Developer Platform

Research OS Developer Platform is a separate application boundary for developers who need temporary, owner-approved access to a user's project resources.

## Separation contract

- **Research OS (regular users)** keeps its existing sign-in and normal owner workflow.
- **Research OS Developer Platform** has a separate application identity, navigation surface and `/v2/developer/*` API namespace.
- A developer authenticates through the configured identity provider first, then requests access to a specific resource.
- The **resource owner must approve** the request before developer access becomes active.
- Approval never transfers ownership, moves the file, renames it, or creates a developer-owned replacement.
- The owner keeps normal read/write access while a developer grant is active.
- The owner may narrow scopes, set expiry, reject a request, or revoke an active grant at any time.
- Developer grants are resource-scoped (`workspace_id + resource_id`) and may contain only `read`, `comment`, and/or `write`.
- Developer access metadata is stored under `RESEARCH_OS_DATA_DIR/developer-access/`; the original resource remains in its canonical owner/source system.

## Identity boundary

The Developer API does **not** trust user-supplied developer IDs. Requests must arrive through a trusted identity gateway that has already authenticated the person and injects the authenticated subject into the backend. Production must configure `RESEARCH_OS_IDENTITY_PROXY_SECRET`; direct untrusted identity headers are rejected.

This keeps authentication replaceable (Google, Microsoft, GitHub, enterprise OIDC, etc.) without making the access-grant store a second identity source of truth.

## Approval flow

1. Developer signs in to Developer Platform through the configured identity provider.
2. Developer selects a resource and submits requested scopes + purpose.
3. Request enters `pending` state; developer still has no resource access.
4. Owner signs in to normal Research OS and reviews the request.
5. Owner approves, narrows, rejects, or later revokes the request/grant.
6. Every developer read/write operation must call the Developer Access Engine before touching the canonical resource.
7. Owner access bypasses developer grants because ownership is unchanged.

## Non-goals

- No copy-on-share file ownership model.
- No developer password database inside Research OS.
- No silent access escalation.
- No permanent write grant by default at the identity layer.
- No changes to the regular user's existing sign-in path.
