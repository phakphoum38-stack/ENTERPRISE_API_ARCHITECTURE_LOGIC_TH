# Research OS API Management Platform

This directory defines the management plane for the Research OS API Platform.

## Ownership

`API_PLATFORM_CONTRACT.yaml` is the platform-owned domain contract. It is intentionally separate from the runtime API contract in `tools/research_os_api/openapi.yaml`.

The management plane owns API ecosystem metadata and lifecycle administration. The existing `ResourceControlPlane` remains the runtime execution authority for authentication, policy, quota, budget, admission, routing, usage accounting, and evidence.

## Management namespace

The reserved management namespace is `/platform/v1`.

It describes management resources such as organizations, projects, applications, APIs, versions, endpoints, scopes, keys, plans, entitlements, products, gateway routes, webhooks, developer-portal metadata, usage, costs, and audit queries.

## Design rule

Do not implement a second policy/quota/budget/admission/evidence engine here. Platform adapters must delegate to the existing runtime kernel.

## Current maturity

See `API_PLATFORM_CAPABILITY_MATRIX.yaml` for capability ownership and maturity. Contract presence does not imply runtime implementation.

## Security boundary

This package does not make the local Research OS API publicly reachable. Production exposure remains a separate deployment/security concern requiring explicit authentication/authorization, TLS, request-size/rate controls, auditability, and network controls.
