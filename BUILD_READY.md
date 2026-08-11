# Research OS — Build Ready Source

This branch is the current build-ready source for Research OS.

## Included

- Research OS Flutter app
  - Minimal AI Chat
  - mobile/desktop navigation
  - Google/Gmail account panel
  - Check-in / Check-out local-first history
- Research OS API
  - provider routing
  - memory and knowledge APIs
  - Google identity sign-in under `/v1/auth/google/*`
  - Google Workspace integration under `/v1/google-workspace/*`
- Owner Friend / Owner Special
  - Friend Python core
  - Flutter Friend desktop
  - Windows ServiceHost
  - installer source
- V3 orchestration/core source
- tests and GitHub Actions workflows

## Google / Gmail production variables

Configure these on the production API host before live Google sign-in:

- `RESEARCH_OS_PUBLIC_BASE_URL`
- `RESEARCH_OS_GOOGLE_IDENTITY_REDIRECT_URI`
- `RESEARCH_OS_GOOGLE_CLIENT_ID`
- `RESEARCH_OS_GOOGLE_CLIENT_SECRET`

For the current Render service the expected identity callback is:

`https://research-os-api-phakphoum.onrender.com/v1/auth/google/callback`

Google Workspace OAuth uses its own callback:

`https://research-os-api-phakphoum.onrender.com/v1/google-workspace/oauth/callback`

## Flutter app build

```bash
cd apps/research_os_flutter
flutter pub get
flutter analyze
flutter test
```

### Windows

```bash
flutter config --enable-windows-desktop
flutter create . --platforms=windows --org com.phakphoum38 --project-name research_os_flutter
flutter build windows --release
```

### iPhone / iOS unsigned build

```bash
flutter create . --platforms=ios --org com.phakphoum38 --project-name research_os_flutter
flutter build ios --release --no-codesign \
  --dart-define=RESEARCH_OS_API_BASE_URL=https://research-os-api-phakphoum.onrender.com
```

Bundle ID used by the Research OS iPhone workflow:

`com.phakphoum38.researchos`

## API tests

From the repository root:

```bash
python -m unittest discover -s tools/research_os_api -p "test_*.py" -v
```

## Friend tests

```bash
python -m unittest discover -s owner_special/tests -p "test_*.py" -v
python owner_special/scripts/smoke.py
```

## Source archive policy

Build-ready source archives are created only from Git tracked files. Generated/runtime directories such as `.dart_tool`, `build`, Python caches, bundled Python runtime, EXE/DLL/PDB output, and CI temporary files are not part of source archives.

Use `.github/workflows/research-os-source-build-ready.yml` to generate the current source packages.