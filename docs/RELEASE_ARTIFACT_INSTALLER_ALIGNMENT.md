# Release Artifact and Installer Alignment

Baseline: `main` @ `a06f0b7`

## Current alignment

| Artifact/contract | Current value | Source | Status |
|---|---|---|---|
| Flutter app package version | `2.0.0-rc.1+1` | `apps/research_os_flutter/pubspec.yaml` | aligned |
| Installer display/package version | `2.0.0-rc.1` | `installer/research-os.iss` | aligned |
| API draft version | `2.0.0-rc.1` | `tools/research_os_api/openapi.yaml` | aligned |
| Active architecture contract | `v3.2.0` | `current/workflow-runtime/` | separate contract version |
| Installer V3 source | `..\v3\*` source to `{app}\v3` | `installer/research-os.iss` | configured |
| Main application payload | `package\*` to `{app}` | `installer/research-os.iss` | configured |
| Research OS data boundary | `%ProgramData%\ResearchOS` | installer and V3 data ownership docs | configured |
| Owner Friend data boundary | `%ProgramData%\ResearchOSOwnerSpecial` | installer | configured |
| Service cleanup | Research OS and Owner Friend uninstall scripts | installer `[UninstallRun]` | configured |

The apparent `v3.2.0` versus `2.0.0-rc.1` difference is intentional: the former versions the active Workflow Runtime architecture contract; the latter versions the current application/API release candidate. They must not be silently normalized without a release/versioning decision.

## Evidence available

- `tools/research_os_api/test_v2_version_alignment.py` verifies Flutter, installer and OpenAPI share `2.0.0-rc.1`.
- V3 architecture and data ownership documents define V3 packaging, loopback service, user isolation and preservation rules.
- `v3/ROADMAP.md` defines clean install, upgrade, uninstall and exact-SHA candidate requirements.
- `BUILD_READY.md` defines Flutter, API and Friend validation commands.
- `tools/validate_release_alignment.py` provides a repeatable source-level version and packaging check.

## Open platform evidence

- Build Flutter Windows release and verify executable path.
- Publish the self-contained Windows ServiceHost and verify the executable.
- Compile/package installer from the exact target SHA.
- Run clean install, service start, loopback/API E2E and user isolation checks.
- Run in-place upgrade and verify user/profile data preservation.
- Run uninstall and verify binaries/services/listeners are removed while data remains.
- Attach candidate manifest, checksums and workflow run IDs to the release commit.

## CI snapshot

On `a06f0b7`, the repository has successful runs for the final gate, unified 10x10 gate, Research OS gate, CI Lite and evidence lineage. No successful `candidate.yml`, Windows artifact or release workflow run was found for this SHA. The Windows installer and exact-SHA candidate evidence therefore remains open.

## Release decision

Source-level alignment is verified. GUI/UX validation and approval are prerequisites before invoking `candidate.yml` or compiling the installer. Production/candidate alignment remains open until Windows installer, service, upgrade/uninstall and exact-SHA evidence pass together. No version metadata should be changed solely to make the contract labels look identical.
