# Research OS — Owner Experimental Workbench

Temporary Owner-only Flutter client for local experimentation.

## Transport

```text
Owner Flutter Workbench
  -> API Platform :8787 /v1/ai/generate
  -> existing Friend bridge :8790 /owner/chat
  -> existing Research OS execution stack
```

The client reuses the existing backend seam. It does not duplicate Memory, AI, Orchestrator, Policy, Admission, Resource Control, Provider, or Evidence.

## Run

```powershell
cd owner_special\experimental_chat
flutter pub get
flutter run -d windows
```

Default API Platform endpoint: `http://127.0.0.1:8787`.

## UI surfaces

- Chat / Work command modes
- Session and mission context
- Execution state and recovery controls
- Workspace / VS Code-oriented control surface
- GitHub repository, branch, PR, CI and evidence control surface
- Evidence, provenance and replay views
- Resource / provider controls
- Audit / forensic timeline
- P0–P10 assurance dashboard
- Raw API response inspector
- Owner-only guard and explicit safety state
- No artificial Research OS chat-message quota

## Important boundary

“No quota” means this experimental client does not add a message/day or conversation cap inside Research OS. Real execution remains governed by the existing Policy, Admission, Resource Control, provider and safety mechanisms. Platform-level limits outside Research OS are unaffected.

UI controls that are not connected to a backend capability are intentionally presented as control surfaces; the client must not fabricate execution, worker activity, CI success, evidence, verification, or PASS states.

## Scope

- Owner-only experimental client.
- Source code only; no installer or release artifact.
- No production integration is required.
- This branch/PR is disposable and can be closed and deleted after the source has been copied locally.
- Do not merge this experiment into `main` unless a separate production integration decision is made.
