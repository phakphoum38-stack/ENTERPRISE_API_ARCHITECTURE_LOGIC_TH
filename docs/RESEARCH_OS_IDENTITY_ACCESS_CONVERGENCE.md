# Research OS Identity & Access Convergence — Wave 1

## Purpose

Wave 1 makes the existing identity and access boundaries explicit and machine-verifiable. It does not replace the current authentication, policy, runtime, or navigation implementations.

## Canonical chain

Identity → Capability → Policy → Authorization → Entitlement → Execution → Evidence

### Existing authority

- Identity/session: `tools/research_os_api/api_auth.py`, `auth_session.py`
- Server-derived context: `tools/research_os_api/identity_context.py`
- Authorization boundary: `owner_special/research_os_friend/policy.py:OwnerPolicy`
- Capability vocabulary: `tools/control_center_capability_registry.py`
- Navigation metadata: `apps/research_os_flutter/lib/src/ui/enterprise_navigation.dart`
- API surface: `apps/research_os_flutter/lib/src/api/research_os_api_client.dart`

## Owner invariant

Owner is server-derived, has the highest privilege, and is not resource/scope bound. Flutter cannot grant or override Owner authority.

## Capability rule

Navigation `capabilityId` is identity metadata only. It is not authorization.

The current navigation destination `google_sign_in` remains **HOLD** because the canonical backend capability registry does not currently prove an `auth` capability with the complete authorization/evidence binding required for promotion.

## Fail-closed behavior

Unknown or invalid identity/authorization is denied. An unproven capability remains HOLD and must not be interpreted as permission.

## What Wave 1 does not do

- No new runtime.
- No new authorization system.
- No duplicate navigation registry.
- No client-side permission grant.
- No promotion of `google_sign_in` into a capability without evidence.

Validation is bound to the Unified Final Gate so the convergence contract cannot silently drift.
