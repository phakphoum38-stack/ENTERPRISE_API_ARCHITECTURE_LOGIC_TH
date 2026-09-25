# Research OS — System / Platform Matrix

## Purpose

This matrix separates systems, platforms, user-facing surfaces, and release/governance contracts so Flutter convergence does not accidentally collapse distinct responsibilities.

## Architectural rule

> One canonical user-facing Flutter Control Center does not mean one system, one runtime, one platform, or one repository language.

Flutter is the presentation/control layer. Platform runners, backend services, Friend runtime, V3 core, evidence, identity, installer, and governance remain independently bounded where their contracts require it.

## Matrix

| Plane | Current implementation | Primary responsibility | Canonical relationship | Migration rule |
|---|---|---|---|---|
| Control Center / UI | `owner_special/flutter_app` | Owner-facing desktop control surface, Friend, Mission/Launch Desk, integrated tools | Target canonical UI shell | Extend existing shell; do not create another desktop shell |
| General Research OS UI | `apps/research_os_flutter` | Cross-platform Research OS application, branding, API/version alignment | Feature source to incorporate | Migrate features/contracts, then retire duplicate UI root only after gates |
| V3 UI | `v3/flutter_app` | V3 desktop surface and V3-specific validation/release behavior | Feature source during convergence | Preserve V3 gates until behavior is incorporated and verified |
| Windows platform | Flutter Windows runners + Owner ServiceHost/installer | Native desktop execution, identity, packaging, service integration | Platform adapter/runtime boundary | Preserve canonical runner identities; never regenerate release runners blindly |
| iOS platform | `apps/research_os_flutter/ios` where committed | iPhone/iOS application target | Platform adapter behind canonical UI | Preserve bundle identity and iOS release gates |
| Android/Web/other platforms | Platform-specific runners as introduced | Platform delivery | Adapter boundary | Add independently; do not duplicate application logic |
| Friend runtime | `owner_special/research_os_friend` | Local-first Owner Friend runtime/service | Shared runtime behind UI contracts | Keep independent from Flutter UI |
| Research OS API | API/service modules | Provider routing, identity, memory/knowledge and integrations | Backend service boundary | UI calls contracts/adapters, not internal implementation |
| V3 core/orchestration | `v3/research_os_v3` | V3 orchestration/core and recovery behavior | Core/runtime boundary | Do not delete while V3 workflows still depend on it |
| Native Core | Control Center workspace + backend contracts | Runtime state/activity/evidence/inspection/simulation | Shared Control Center capability | Reuse existing workspace; no second runtime |
| GitHub Workbench | Current Owner Control Center integration | GitHub inspection/workbench capabilities | Control Center feature module | Reconcile into canonical shell; tests stay contract-bound |
| Universal Control Surface | `tools/universal_control_surface.py` + contract | Read-only search/inspection, lineage/Why trace, system map, command preparation | Control/governance service | Command preparation is not execution; authority remains external |
| Identity / Authority | manifests, authority/evidence gates | Identity, authorization and release boundaries | Cross-plane governance | Never bypass with UI consolidation |
| Provenance / Evidence | `current/`, provenance tools and ledgers | Proof lineage, hashes, evidence | Cross-plane assurance | Do not rewrite or relocate canonical evidence casually |
| Installer / Release | Owner installer + Research OS release workflows | Packaging, clean install, upgrade, uninstall/data preservation | Platform/release boundary | Migrate only after artifact and E2E gates remain equivalent |
| CI / Gates | GitHub Actions | Build, test, identity, platform and release assurance | Cross-plane verification | Consolidate only after equivalent coverage is proven |
| Runtime resolution | `current/RESEARCH_OS_PLATFORM_RUNTIME_RESOLUTION_CONTRACT.json` | Resolve validated surface/capability/path into compatible local runtime/resource context | Platform-owned boundary consumed by Flutter | Do not move resolution authority into Flutter; preserve shared Queue/Runner |
| Unified UX / Light Beam | `current/RESEARCH_OS_UNIFIED_UX_LIGHT_BEAM_CONTRACT.json` | Shared visual language, tokens, semantic states and light-beam interaction effects | Platform-owned UX contract consumed by Windows/Web/iOS | Do not create per-surface primary palettes; legacy UX must be migrated or explicitly compatibility-scoped |

## Flutter convergence target

```text
                    RESEARCH OS
                         |
                 CANONICAL CONTROL CENTER
                         |
          +--------------+--------------+
          |              |              |
        Friend       GitHub         Native Core
                       Workbench
          |              |              |
          +--------------+--------------+
                         |
                Shared Contracts
                         |
          +--------------+--------------+
          |              |              |
       Windows          iOS        Other Platforms
          |              |              |
       adapters       adapters      adapters
          +--------------+--------------+
                         |
              Runtime / API / Core
                         |
          Evidence / Identity / Governance
```

## Current non-negotiable boundaries

1. `owner_special/flutter_app` remains the existing Owner/Control Center desktop shell during migration.
2. `apps/research_os_flutter` remains the source of general cross-platform Research OS UI capabilities until those capabilities are migrated and verified.
3. `v3/flutter_app` remains protected by its V3 validation/build contracts until V3 behavior is incorporated.
4. Owner Special Windows identity and installer contracts remain intact.
5. Platform runners are not treated as duplicate application systems merely because they contain Flutter-generated files.
6. Backend/runtime/core code is not moved into Flutter merely to achieve a single UI root.
7. Path resolution and runtime/resource selection remain Platform-owned and contract-backed; Flutter consumes the result.
8. Unified UX tokens and semantic states are Platform-owned; Windows/Web/iOS consume the same visual contract.
9. No Git history rewrite, force push, reset, or provenance/baseline alteration is part of convergence.

## Verification gates before retiring a UI root

A duplicate Flutter application root may only be retired after all applicable items are demonstrated:
- feature parity / explicit feature disposition;
- tests moved or replaced with equivalent coverage;
- assets and branding preserved;
- platform runner identity preserved;
- API/version contracts preserved;
- Windows build and startup E2E preserved;
- Owner identity/installer/provenance gates preserved;
- V3 gates no longer require the retired root;
- CI references no longer require the retired root;
- exact-source and evidence lineage remain auditable.

## Immediate next work

The next implementation unit is contract extraction and feature mapping, not deletion:
1. map each screen/service in the three Flutter roots;
2. classify it as `canonical`, `migrate`, `adapter`, `platform-only`, or `retire`;
3. identify shared models/contracts;
4. wire migrated capabilities into the existing Control Center;
5. keep legacy roots as compatibility gates until verification closes them.

This matrix is an architecture control document; it does not authorize deletion or merge by itself.

## Flutter convergence map binding

The file `current/RESEARCH_OS_FLUTTER_CONVERGENCE_MAP.json` is the executable feature-disposition map for the three Flutter roots. It is descriptive and fail-closed: it does not authorize deletion.

- `owner_special/flutter_app` — canonical Owner / Control Center shell; preserve Windows identity and installer boundaries.
- `apps/research_os_flutter` — feature source; migrate general Research OS capabilities and shared UI/contracts into the canonical shell.
- `v3/flutter_app` — compatibility source; preserve V3 startup/API behavior and gates until convergence evidence closes them.
- Classification vocabulary is limited to `canonical`, `migrate`, `adapter`, `platform-only`, and `retire`.
- Current root-level retirement authorization is explicitly **false**.
- Validation: `python tools/validate_research_os_flutter_convergence_map.py` and `python -m unittest tools/test_validate_research_os_flutter_convergence_map.py -v`.

The convergence map must be updated before any future root-retirement proposal so feature parity, tests, assets, runner identity, API/version contracts, E2E, installer/provenance, and CI references remain auditable.
