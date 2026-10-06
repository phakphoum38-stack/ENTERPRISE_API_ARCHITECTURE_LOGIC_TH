# Research OS API Credential Quickstart

## Status

The Research OS Platform already contains the canonical API credential lifecycle and the governed execution boundary. This document is the developer-facing entry point.

## What a user can do

1. Authenticate to the Research OS account with the canonical session.
2. Create an application under the API Management Platform.
3. Bind the application to an entitlement and scopes.
4. Create a machine credential for the application.
5. The raw secret is returned only at creation or rotation time and is never persisted.
6. Use the credential against the governed resource-control execution boundary.
7. Revoke or rotate the credential without changing the user identity.

## Management endpoints

All management endpoints require a valid Research OS session.

- POST /platform/v1/organizations
- POST /platform/v1/projects
- POST /platform/v1/applications
- POST /platform/v1/scopes
- POST /platform/v1/plans
- POST /platform/v1/plans/{plan_id}/entitlements
- POST /platform/v1/applications/{application_id}/keys
- GET /platform/v1/applications/{application_id}/keys
- POST /platform/v1/applications/{application_id}/keys/{key_id}/rotate
- POST /platform/v1/applications/{application_id}/keys/{key_id}/revoke

The key must have scopes contained by its effective entitlement. A raw secret is never a management object.

## Runtime use

The canonical runtime control boundary accepts the issued machine credential, resolves the principal, checks the requested scope against the credential and entitlement, and then passes execution through admission, quota, budget, routing, usage accounting and evidence.

A client should send its credential only over TLS to the production API. Do not place the raw secret in source control, logs, URLs, browser local storage, or client-side telemetry.

## Credential lifecycle

- Create: receive the raw secret once.
- Store: keep it in the caller's secret manager.
- Verify: the platform compares a derived credential digest.
- Rotate: the old credential is revoked and a replacement is returned once.
- Revoke: the credential can no longer authenticate.
- Expire: an optional expiry timestamp fails closed.

## Architecture boundary

The management plane owns API/application/key metadata and lifecycle. The existing Research OS runtime control plane remains the authority for authentication, authorization, entitlement, quota, budget, admission, routing, execution, usage accounting and evidence.

No second policy or execution authority is introduced by API credentials.
