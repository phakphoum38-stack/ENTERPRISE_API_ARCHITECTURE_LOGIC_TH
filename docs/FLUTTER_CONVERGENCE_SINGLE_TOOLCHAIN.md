# Flutter convergence: one UI, one Dart toolchain

## Decision

Research OS will converge its Flutter surfaces through a staged bridge instead of deleting or
copying the three existing applications in one operation.

The current surfaces are:

- `apps/research_os_flutter` — general Research OS application, branding/version/standard CI
  integration.
- `owner_special/flutter_app` — Owner Special / Control Center desktop shell and Friend
  integration.
- `v3/flutter_app` — V3 desktop surface and its dedicated release gates.

All three currently declare the same Dart SDK compatibility range (`>=3.4.0 <4.0.0`).
Therefore the immediate collision is architectural/source-root duplication, not an incompatible
Dart SDK constraint.

## Target architecture

```
                         Research OS
                              |
                     Canonical Control Center
                              |
                    shared contracts/adapters
                    /           |            \
                 Friend    GitHub Workbench   V3
                    \           |            /
                     shared runtime/API/core
```

The canonical user-facing shell is the Control Center surface. Existing application roots remain
intact during migration.

## Rules

1. Do not delete any Flutter root until its features, tests, assets, platform runners, installers,
   and CI references have been migrated and verified.
2. Do not combine incompatible Dart source trees merely because their SDK constraints overlap.
   Shared code must cross an explicit contract/adapter boundary.
3. The migration must preserve the existing Owner Special Windows identity/installer contract.
4. The migration must preserve the standard Research OS branding, API/version alignment, and
   platform gates.
5. V3 release gates remain valid until V3 behavior has been incorporated into the canonical shell.
6. No Git history rewrite, reset, force-push, or modification of provenance/baseline evidence is
   part of this migration.
7. CI must eventually have one canonical UI build/test root, with compatibility gates for any
   temporary legacy surface.
8. The final state is one user-facing Flutter application and one canonical Flutter/Dart toolchain;
   the migration may use temporary adapters while convergence is in progress.

## Migration stages

1. Inventory dependencies and CI references.
2. Establish shared contracts/adapters.
3. Bring Control Center, Friend, GitHub Workbench, Native Core and Universal Control Surface into
   the canonical shell.
4. Bring required V3 behavior into the same shell without creating a second execution path.
5. Move tests and build/release workflows to the canonical root.
6. Verify Windows/iOS/application identity and release contracts.
7. Retire duplicate Flutter roots only after all gates pass.

## Current baseline observations

As of the migration starting point:

- all three Flutter projects declare `>=3.4.0 <4.0.0`;
- `apps/research_os_flutter` is referenced by the standard Flutter CI, Windows artifact,
  iOS artifact, branding, and API/version alignment checks;
- `owner_special/flutter_app` is referenced by the Owner Special identity/installer pipeline and
  the existing Control Center/Mission Control work;
- `v3/flutter_app` is referenced by dedicated V3 validation/build workflows.

These references are intentionally not removed by this first convergence step.
