# Research OS V3 Flutter Desktop

Clean desktop shell for the V3 architecture.

## Contract boundary

The app only talks to the loopback V3 service:

- `GET /health`
- `GET /v3/master`
- `GET /v3/providers`

The desktop process never reads or stores provider API keys. Provider status is a safe service contract with `secret_exposed=false`.

## Startup proof

`main.dart` paints the UI first, then runs a best-effort startup probe that calls both `/health` and `/v3/providers`. CI launches the compiled Windows EXE against the real V3 service and verifies those requests from the service's structured audit log.

## Local development

```powershell
cd v3/flutter_app
flutter create --platforms=windows --project-name=research_os_v3_flutter .
flutter pub get
flutter run -d windows
```

Run `python v3/scripts/run_service.py` from the repository first.
