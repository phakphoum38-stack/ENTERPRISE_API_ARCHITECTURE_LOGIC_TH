# Research OS Branding Source of Truth

`research_os_master.webp` is the canonical Research OS branding asset for generated platform icons.

## Contract

- Do not hand-edit generated platform icons as an independent source of truth.
- Windows, Android, iOS, macOS, Web, and Linux icon outputs must be generated from the canonical master through `scripts/apply-research-os-branding.py`.
- Installer and executable branding must remain consistent with the same master asset.
- Branding validation in CI is evidence of generation/packaging coverage; it does not alter application ownership, release state, or publication state.

## RC hardening

Release-candidate hardening must validate branding on the exact candidate SHA before promotion. A branding-only validation does not authorize merge, tag creation, GitHub Release publication, or production deployment.
