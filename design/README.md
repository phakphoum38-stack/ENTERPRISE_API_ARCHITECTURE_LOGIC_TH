# Research OS GUI/UX Design Assets

This directory is the handoff boundary between visual design and the Research OS UI implementation pipeline.

## Structure

```text
design/
├── concepts/
├── artwork/
├── icons/
├── backgrounds/
├── exports/
│   ├── png/
│   └── psd/
├── manifest/
└── README.md
```

## Toolchain

- **ibisPaint**: visual artwork, illustration, icons, backgrounds, concept art.
- **Figma**: UI composition, components, spacing, typography, interaction and design-system handoff.
- **Flutter / Research OS**: implementation.
- **CI/E2E**: validation after implementation.

## Asset flow

```text
ibisPaint → PNG/PSD → asset validation → Figma → Flutter → E2E/visual regression → evidence
```

## Naming convention

Use lowercase kebab-case and a semantic prefix:

- `concept-<name>.png`
- `icon-<name>.png`
- `background-<name>.png`
- `<name>.psd`

## Validation contract

Before an asset enters the UI implementation pipeline, verify:

1. file is readable and not corrupted;
2. extension matches the actual asset type;
3. dimensions are intentional and documented where needed;
4. transparent assets use PNG where appropriate;
5. editable artwork remains PSD when layer preservation matters;
6. filenames are deterministic and semantic;
7. no temporary/export-cache files are committed.

## CI isolation

Do not install or execute ibisPaint or Figma in GitHub Actions. They are authoring tools used outside CI. CI consumes validated repository assets and metadata only.

This design boundary is intentionally isolated from the current `research-os-gate` and `generate-orchestrator` startup-failure investigation.
