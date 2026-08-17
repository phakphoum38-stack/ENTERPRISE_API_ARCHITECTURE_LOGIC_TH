# Research OS Notification & Update Center

Status: implementation contract

## Product rule
Users must not need to browse for installer files, unzip artifacts, open PowerShell, or manually compare SHA-256 during normal updates.

## User flow
1. Research OS checks update metadata in the background.
2. Notification Center shows a badge when an update is available.
3. Update card displays version, verification state, release notes, and action.
4. User presses **Install now**.
5. Research OS downloads the matching installer and checksum/manifest automatically.
6. Research OS verifies SHA-256 automatically.
7. Hash mismatch: STOP, show a clear error, never launch the installer.
8. Hash verified: launch the installer with Windows elevation; Windows owns the UAC consent screen.
9. UI reports Waiting for permission / Installing / Restarting service / Verifying health / Completed.
10. After upgrade, persistent owner Memory/Data remains separate and preserved.

## Notification states
- update_available
- downloading
- verifying
- verified
- waiting_for_uac
- installing
- restarting_service
- verifying_health
- completed
- failed
- hash_mismatch

## UI requirements
- Notification/bell badge with unread count.
- Dedicated Updates view reachable from Notification Center.
- Primary action: Install now.
- Secondary actions: Later, View details.
- Progress/status must be visible without requiring logs.
- Errors include a human-readable recovery action.
- Do not ask the user to find Setup.exe manually during the normal flow.

## Security/integrity
Each build/version owns its checksum. A new version is not required to match an old version's SHA-256. The downloaded installer must match the manifest for that exact build before execution. Research OS must never bypass Windows UAC or weaken Windows security settings.

## Data preservation
Installer binaries and update metadata are replaceable delivery assets. Persistent Research OS owner data, Memory, profiles, and durable configuration must remain separate from application binaries and be preserved according to the recovery policy.

## Acceptance gates
- Update badge/card appears for an available update.
- Install now drives download -> verify -> elevation -> install without manual file hunting.
- Deliberate checksum mismatch is blocked.
- Successful upgrade verifies service health after installation.
- Upgrade preserves persistent owner data.
- Failure is visible in Notification Center and retry is possible.
