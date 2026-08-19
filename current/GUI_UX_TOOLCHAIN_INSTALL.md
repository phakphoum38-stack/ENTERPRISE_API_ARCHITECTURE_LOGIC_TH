# GUI/UX Toolchain Installation Guide

## Purpose
Use ibisPaint as the visual artwork authoring tool and Figma as the UI composition/design-system tool. Keep both outside GitHub Actions; Git stores source/exported assets and metadata only.

## 1. Install ibisPaint

Official site (Thai): https://ibispaint.com/?lang=th

### Windows
1. Open the official ibisPaint site.
2. Select the Windows product/download option.
3. Download the installer from the official source.
4. Run the installer and complete setup.
5. Launch ibisPaint and create a test canvas.

### iPhone/iPad
1. Open the App Store.
2. Search for `ibis Paint` or `ibis Paint X`.
3. Install the official ibisPaint app.
4. Create a test canvas and verify export.

## 2. Project asset layout

Create/use this structure in the Research OS project:

```text
design/
  concepts/
  artwork/
  icons/
  backgrounds/
  exports/
    png/
    psd/
  manifest/
```

## 3. Export workflow

```text
ibisPaint
  -> artwork / icon / background
  -> export PNG or PSD
  -> design/exports/
  -> asset validation
  -> Figma composition
  -> Flutter / Research OS implementation
  -> build
  -> E2E / visual regression
  -> evidence
```

## 4. Git rules

- Do not install ibisPaint or Figma on GitHub Actions runners.
- Do not make ibisPaint/Figma runtime dependencies of Research OS.
- Commit only required design sources/exports and metadata.
- Prefer PSD for editable artwork and PNG for runtime assets.
- Validate dimensions, file type, naming, and integrity before UI build.

## 5. Six GUI logical lanes

- GUI-01: visual concept
- GUI-02: artwork/assets
- GUI-03: asset validation
- GUI-04: Figma composition/design system
- GUI-05: Flutter/UI implementation
- GUI-06: visual regression/E2E

These are logical orchestration lanes under the 6^6 model, not 46,656 physical workers.

## 6. Safety rule for the current CI investigation

The GUI/UX toolchain must remain isolated from the current `research-os-gate` / `generate-orchestrator` startup-failure investigation. Do not add design-tool dependencies to those workflows while root cause is unresolved.
