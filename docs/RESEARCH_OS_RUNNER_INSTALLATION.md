# Research OS Universal Runner — Installation & Bootstrap

## Purpose
The installation layer turns a verified Research OS package from a local or cloud-synchronized source into a local Universal Runner installation.

**Cloud Drive is distribution, not runtime.**

The installer does not authorize work, grant entitlement, schedule jobs, execute workflow work, publish releases, or maintain a second evidence ledger.

## Bootstrap
DISCOVER → DOWNLOAD → VERIFY → STAGE → INSTALL → REGISTER → DISCOVER_CAPABILITIES → HEALTH_CHECK → READY

## Cloud Drive
Supported pattern:

Cloud Drive → Bootstrap → Local Install → Universal Runner

Execution directly from a synchronized folder is avoided because synchronization can expose partial files, locking, version skew, and concurrent modifications.

After installation, the local runtime can operate without the Cloud Drive being mounted.

## Existing Windows installer
The canonical Windows installer remains `installer/research-os-unified.iss`. This contract does not create a second Windows installer authority.

## Integrity
A package manifest binds package ID, version, platform, architecture, source commit SHA, artifact SHA-256, and per-file SHA-256 entries. Digest mismatch, unsafe paths, missing identity, or unsupported platform/architecture are rejected.

## Safety
- Failed verification never installs.
- Failed installation never advertises READY.
- Installation does not delete unrelated user data.
- Registration does not grant authorization or entitlement.
- Unknown capabilities remain unavailable.
- Unified Final Gate remains the only release authority.

## Multi-platform
Profiles cover Windows x64, Linux x64, macOS arm64, and portable packages. Boot/provisioning remains profile-driven.

## Offline
Cloud is a distribution source. Local installation is the runtime boundary; reconnect reconciliation remains outside the installer.
