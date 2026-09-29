# GUI/UX Audit Status

Baseline: `main` @ `a06f0b7`

## Verified in this environment

- Flutter app surfaces and widget tests are present under `apps/research_os_flutter/`.
- Responsive implementation uses `LayoutBuilder`, `SafeArea`, overflow constraints and platform-aware sizing in the inspected surfaces.
- Accessibility semantics are present in check-in and agent-center flows.
- `design/validate_assets.py` passes.
- `.github/workflows/gui-ux-validation.yml` protects GUI/UX changes with asset validation, Flutter analyze and widget tests; it does not build or release the installer.
- The design asset manifest is intentionally empty because its rules accept only real handoff assets under `design/`; the app branding WebP remains an implementation asset under `apps/research_os_flutter/assets/`.

## Required GUI/UX validation before setup.exe

- Run `flutter analyze`.
- Run all Flutter widget tests.
- Run Windows and mobile viewport checks for navigation, chat, home, library, agents, monitor, settings, Google Workspace and check-in flows.
- Review text overflow, keyboard/inset behavior, accessibility labels and loading/error/empty states.
- Run visual regression or capture an approved baseline.
- Record screenshots and test evidence against the target commit SHA.

## Platform limitation

The current Linux container does not provide Flutter/Dart, so Flutter analyze, widget tests, Windows build and screenshot-based visual regression cannot be completed here. Do not build or release `setup.exe` until the GUI/UX gates above are reviewed and approved.

## Release rule

GUI/UX approval is a prerequisite to Windows candidate and installer build. The GUI/UX workflow is a pre-release check only and does not authorize a release build by itself.
