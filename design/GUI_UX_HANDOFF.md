# GUI/UX Handoff Contract

## Goal

Define the handoff boundary from visual design to Research OS implementation without coupling design authoring tools to CI runtime.

## Source of truth

- **ibisPaint**: artwork and visual assets.
- **Figma**: UI layout, components, interaction, typography, spacing, and design-system decisions.
- **Repository**: approved exports, asset manifest, implementation contract, and evidence.

## Handoff sequence

```text
Design brief
  ↓
ibisPaint artwork
  ↓
PNG / PSD export
  ↓
asset manifest + validation
  ↓
Figma UI composition
  ↓
component/state specification
  ↓
Flutter / Research OS implementation
  ↓
visual regression + E2E
  ↓
evidence
```

## Required handoff data

Every production UI screen should identify:

1. screen name and stable ID;
2. target platform(s);
3. viewport/responsive constraints;
4. typography tokens;
5. spacing/layout rules;
6. component states;
7. interaction states;
8. referenced asset paths from `design/manifest/assets.json`;
9. accessibility expectations;
10. visual-regression reference where applicable.

## Implementation rule

Implementation must consume the contract, not screenshots alone. If a design decision is ambiguous, mark it as `UNRESOLVED` rather than inventing behavior.

## Validation gates

```text
asset validation
  ↓
handoff contract validation
  ↓
implementation
  ↓
build
  ↓
visual regression
  ↓
E2E
```

A failed design gate must not silently become a code workaround.

## CI isolation

This contract does not install or execute ibisPaint/Figma in GitHub Actions. CI validates repository artifacts and implementation outputs only. Keep this pipeline isolated from the current `research-os-gate` and `generate-orchestrator` startup-failure investigation until those workflows are stable.
