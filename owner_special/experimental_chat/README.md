# Research OS — Owner Experimental Chat

Temporary Owner-only Flutter client for local experimentation.

## Path

```text
Flutter
  -> API Platform :8787 /v1/ai/generate
  -> existing Friend bridge :8790
  -> existing Research OS execution stack
```

The API Platform currently routes the default AI generation path through the existing Friend service; this client does not duplicate Memory, AI, Orchestrator, Policy, Admission, Resource Control, Provider, or Evidence.

## Run

```powershell
cd owner_special\experimental_chat
flutter pub get
flutter run -d windows
```

The default endpoint is `http://127.0.0.1:8787`. It can be changed in the UI.

## Scope

- Owner-only experimental client.
- Source code only; no installer or release artifact.
- No production integration is required.
- This branch/PR is disposable and can be closed and deleted after the source has been copied locally.
