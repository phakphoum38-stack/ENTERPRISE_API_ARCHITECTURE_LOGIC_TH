# Research OS Self-Build Virtual Lab

## Purpose

Teach Research OS to create a validated copy of its own source tree inside an isolated virtual build workspace, then prove that the copy can pass V3 tests and compile Windows artifacts.

This is **not** uncontrolled self-replication. The source tree remains read-only from the self-build component. The lab does not merge, deploy, publish, install, modify the original workspace, or execute arbitrary code discovered from storage.

## One-Truth architecture

```text
Canonical Research OS source
        |
        v
ResearchOSSelfBuilder
        |
        +--> policy / path confinement
        +--> generated/cache/secret exclusions
        +--> required-path validation
        +--> SHA-256 source manifest
        +--> skill/tool capability snapshot
        |
        v
Fresh virtual workspace
        |
        +--> V3 unit tests
        +--> Flutter analyze/test
        +--> Flutter Windows release EXE
        +--> Windows ServiceHost EXE
        |
        v
SELF_BUILD_EVIDENCE.json + CI artifact
```

## Tool-discovery skills taught to Research OS

The self-build manifest records the process Research OS should follow when it needs a tool:

1. **analysis** — understand intent, constraints, and capability needed.
2. **research** — inspect available Skill/Tool registries and governed integrations.
3. **governed-tool-execution** — match capability to a native tool and read its risk metadata.
4. **security** — verify permission and approval before writes.
5. **drive-tools-list** — only when native tools are insufficient, discover checksum-governed packages from the configured local Google Drive mirror.
6. **planning** — choose the smallest bounded plan; logical 10^10 capacity must never mean eager 10^10 execution.
7. **quality** — validate outputs, hashes, tests, and evidence before artifact promotion.

## Safety boundaries

- Output workspace must be outside the canonical source tree.
- Existing output directories are refused rather than overwritten.
- Symlink inputs are refused.
- `.git`, build products, package caches, virtual environments, Dart caches, `node_modules`, and Python caches are excluded.
- `.env`, credential/secrets JSON files, private key/certificate container suffixes are excluded.
- Required V3 core, Flutter, and ServiceHost paths must exist or staging fails closed.
- Every staged file is recorded with byte size and SHA-256.
- Write/risky tools remain approval-gated by the existing V3 tool registry.
- The self-build lab never creates a second Unified Master.

## Running locally

From the repository root, choose a fresh output path outside the repository:

```powershell
python v3/scripts/self_build_lab.py `
  --source "$PWD" `
  --workspace "D:\research-os-self-build" `
  --source-sha "$(git rev-parse HEAD)"
```

The output root contains `SELF_BUILD_MANIFEST.json` plus the staged source tree.

## CI proof

Workflow: `.github/workflows/v3-self-build-lab.yml`

The Windows runner stages the project into a fresh `D:\research-os-self-build` workspace, runs V3 tests from that copy, generates/validates the Windows Flutter platform files in that copy, builds the Flutter Windows release executable, publishes the .NET ServiceHost, calculates artifact hashes, and uploads the self-build proof as a GitHub Actions artifact.
