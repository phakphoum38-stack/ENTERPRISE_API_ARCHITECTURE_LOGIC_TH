# Research OS Baseline

Status: BASELINE READY

## Three synchronized locations

1. GitHub — source and version control
2. Research OS Flutter — client/UI integration
3. Google Drive — workspace/storage

## Integration

- Research OS Flutter -> Research OS API
- Research OS API -> OpenAI / ChatGPT control layer
- Research OS Flutter -> Google Workspace connector
- Google Workspace connector -> Google Drive

## Safety gates

- Do not overwrite preserved V1 data.
- Do not modify PR #47.
- Credentials remain backend-only.
- Build and installation require evidence checks.

Recorded baseline: 2026-08-16
