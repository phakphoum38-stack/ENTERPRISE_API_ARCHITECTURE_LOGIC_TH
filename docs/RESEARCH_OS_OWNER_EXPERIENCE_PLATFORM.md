# Research OS Owner Experience Platform

## Purpose
The Owner Experience Platform makes the Owner surface one coherent product/platform boundary across Windows, Web, and iOS.
The canonical product UI is apps/research_os_flutter. Owner Special remains an existing runtime boundary; it is not a second product UI, navigation authority, authorization authority, evidence ledger, or release authority.

## Canonical shape
Research OS
├── Canonical UI: apps/research_os_flutter
│   ├── Shared navigation registry
│   ├── Owner Workspace
│   ├── Windows adapter
│   ├── Web adapter
│   └── iOS adapter
└── Owner Special runtime boundary
    ├── Friend/runtime
    ├── Native integration
    ├── Windows ServiceHost
    └── Installer

Owner identity remains server-derived from /v1/auth/status. Owner is the highest privilege and is not constrained by resource or scope. The UI only observes the authority; it cannot grant, authorize, approve, execute, merge, or release.

## UI reconciliation
The shared enterprise_navigation.dart registry remains the only canonical navigation registry. Desktop and mobile consume it. Semantic V5 navigation is a projection/migration layer, not another source of truth.
The Owner Special Flutter shell is treated as a runtime compatibility surface. Its pages may continue to exist where needed by the runtime/installer pipeline, but they must not define a competing product navigation model.

## iOS reconciliation
There is no Owner Special iOS product source in the canonical tree. The iOS product surface is apps/research_os_flutter/ios.
The previous Owner Special iOS workflow becomes a reconciliation guard only. It must not build from owner_special/flutter_app, mutate an Owner Special iOS project, or create a second iOS product identity.
The canonical iOS workflow validates the same shared Research OS application surface used by Windows/Web.

## Flexibility rule
Platform adapters may differ where the OS requires it (native runner, signing, packaging, lifecycle), but user-facing capability identity, navigation identity, Owner authority semantics, and release authority must remain aligned.

## Assurance
Required proof: tools/validate_owner_experience_platform.py; tools/test_owner_experience_platform.py; apps/research_os_flutter/test/owner_experience_page_test.dart; apps/research_os_flutter/test/platform_surface_parity_test.dart; canonical iOS workflow; Owner Special Windows identity/installer gates; Unified Final Gate.
UNKNOWN, DEFERRED, or stale platform evidence is not treated as PASS.
