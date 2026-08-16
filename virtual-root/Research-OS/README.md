# Research OS — Virtual Root

This directory is the project workspace beneath the Connector layer.

## Canonical structure

- `source-code/` — source kept separate from generated artifacts
- `project-modules/` — modular Research OS components
- `platforms/` — platform-specific work
- `builds/` — generated build outputs
- `releases/` — release candidates and final releases
- `evidence/` — verification evidence, hashes, and gate results

## Flow

Connector → Virtual Root → Research OS → Project Modules
