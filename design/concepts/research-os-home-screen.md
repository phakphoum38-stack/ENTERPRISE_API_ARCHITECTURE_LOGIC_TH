# Research OS — First GUI/UX Screen Brief

Status: DRAFT / READY FOR VISUAL AUTHORING

## Goal
Define the first screen to be authored visually in ibisPaint/Figma without coupling the design to runtime or CI implementation details.

## Screen
**Research OS Home / Master Workspace**

## Primary regions

1. **Top bar**
   - Research OS identity
   - current workspace/context
   - connection/status indicator

2. **Master workspace**
   - primary work area
   - current task/case summary
   - clear primary action

3. **Orchestration panel**
   - 6 logical lanes
   - status per lane
   - bounded execution indicator

4. **Evidence panel**
   - latest evidence/case state
   - validation status
   - link to detailed evidence

5. **Assistant area**
   - conversation/task input
   - action feedback
   - no API-key details exposed in the visual UI

## Visual authoring split

### ibisPaint
Use for:
- background artwork
- assistant/mascot artwork if desired
- decorative illustrations
- custom icons or visual assets

Export editable artwork as PSD and runtime-ready assets as PNG where appropriate.

### Figma
Use for:
- layout
- components
- spacing
- typography
- interaction states
- responsive behavior
- design-system handoff

## Initial states

- `idle`
- `working`
- `success`
- `warning`
- `error`
- `unresolved`

`unresolved` must be visually explicit and must not be represented as success.

## Accessibility baseline

- readable text hierarchy
- keyboard/focus states where applicable
- sufficient contrast
- status must not rely on color alone
- important actions have clear labels

## Handoff requirements

Before implementation, the Figma handoff should define:

- desktop layout
- responsive layout
- component/state inventory
- asset references from `design/manifest/assets.json`
- typography tokens
- spacing tokens
- interaction notes
- unresolved decisions

## Implementation boundary

This is a design brief only. Do not add ibisPaint or Figma as GitHub Actions dependencies. Do not modify `research-os-gate` or `generate-orchestrator` as part of this design task.
