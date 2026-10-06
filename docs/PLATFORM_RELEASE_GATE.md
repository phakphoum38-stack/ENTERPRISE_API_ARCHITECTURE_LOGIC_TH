# Research OS Platform Release Gate

## Purpose

The platform release gate proves that Research OS identity, session, authorization, execution, and evidence boundaries remain converged before a production capability is promoted.

The gate does not grant authority. It verifies that the implementation follows authority already defined by the owner and existing server-side policy.

## Authority chain

```text
External Identity Provider
        |
        v
Identity Broker
        |
        v
Research OS Session
        |
        v
Identity Context
        |
        v
OwnerPolicy / Capability Registry
        |
        v
Resource Control Plane
        |
        v
Execution + Evidence
```

No client, UI, provider, or capability registry entry may become an execution or authorization authority by inference.

## Release phases

| Phase | Gate | Required evidence |
|---|---|---|
| 0 | Authority boundary | Existing canonical authority map and fail-closed contract |
| 1 | Production identity | Exact deployed SHA, deployment evidence, live health |
| 2 | OIDC hardening | PKCE S256, nonce, signed ID-token validation, issuer/audience/expiry checks |
| 3 | Session platform | Server-derived signed session, expiry, revocation |
| 4 | Account linking | Explicit verified linking; no implicit merge |
| 5 | Authorization convergence | OwnerPolicy and capability proof; client cannot grant |
| 6 | Machine identity | API credentials remain separate from execution authority |
| 7 | Multi-provider | Provider adapters converge on the same Research OS identity/session boundary |
| 8 | Evidence plane | Security-sensitive actions are provenance-bound |
| 9 | Reliability | health/readiness/HEAD probes and safe observability |
| 10 | CI security gates | Automated positive and negative security checks |
| 11 | Platform release | All required evidence bound to one canonical release SHA |

## Hard fail conditions

The release gate must fail closed when any of the following is observed:

- client-supplied identity is trusted as authoritative;
- client or UI can grant or override authorization;
- OAuth state is missing, expired, or reusable;
- PKCE or nonce validation is missing;
- ID-token signature, issuer, audience, expiry, or nonce validation fails;
- Google identity subject/email does not match the verified ID token;
- OAuth secrets appear in URLs, logs, or client assets;
- a new authorization or execution runtime is introduced;
- production deployment SHA cannot be bound to the tested source;
- required runtime evidence is missing.

## Current implementation target

Google production authentication is the first provider used to prove the platform boundary.

The production callback is:

`https://research-os-api-phakphoum.onrender.com/v1/auth/google/callback`

The provider remains an identity source. Research OS remains the canonical session and authorization boundary.

## Phase 11 acceptance

Phase 11 may only be marked `PLATFORM_RELEASE_READY` when:

1. Phase 0 through Phase 10 are proven.
2. Production deployment is live and its exact SHA is recorded.
3. Real Google login succeeds in production.
4. `/v1/auth/status` reports server-derived identity.
5. Invalid/replayed/expired authentication state is denied.
6. Forged/expired/revoked Research OS sessions are denied.
7. No secret or session credential leaks through URL/log/client assets.
8. The final release commit is the same commit whose checks and evidence passed.
9. The evidence packet is immutable and linked to the canonical history.

Until all nine conditions are proven, the status is `PLATFORM_RELEASE_HOLD`, not ready.

## Operating rule

All implementation changes follow:

```text
READ
  -> ANALYZE
  -> WRITE / MODIFY
  -> TEST
  -> AUDIT
  -> EVIDENCE
  -> COMMIT / PUSH / MERGE
```

No destructive history rewrite is part of the release process.
