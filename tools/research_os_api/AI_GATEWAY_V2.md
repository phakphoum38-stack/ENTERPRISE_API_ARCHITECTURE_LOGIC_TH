# Research OS AI Gateway v2

## Goal

Separate provider detection, credential handling, provider selection and UI status so Research OS can use local or configured AI providers without hard-coding one vendor in Flutter.

## Selection order

1. Explicit `RESEARCH_OS_PROVIDER` when it is not `auto`.
2. Ready local OpenAI-compatible provider.
3. Gemini.
4. Anthropic.
5. OpenAI-compatible remote provider.
6. Built-in mock fallback.

CI skips ambient localhost discovery by default so an unrelated service on a runner cannot change test behavior.

## Credential boundary

`credential_broker.py` is the only Research OS-owned credential resolver used by the provider construction path.

- Existing environment variables remain compatible.
- Windows persisted credentials use machine-scope DPAPI.
- Credential values are never returned by gateway status reports.
- Arbitrary application credential files are not scanned.
- Flutter does not store or display AI provider secrets.

The secure-store write API is intentionally not exposed remotely in this slice. A future local-management endpoint must prove loopback authentication/authorization before accepting secrets.

## API

`GET /v2/providers` returns a secret-safe gateway report containing:

- selected provider, source and reason
- provider state (`available`, `needs_setup`, `offline`)
- detection source
- readiness and credential-presence booleans
- local endpoint when applicable
- registry capabilities

## Flutter

Chat requests no longer hard-code Gemini. When no provider is passed, the backend AI Gateway resolves the provider. Settings uses the V2 gateway report for Provider Manager status.

## Release safety

This work is isolated on `hardening/v2-rc2-ai-gateway`, based on frozen RC1. It does not change RC1 history, merge `main`, create a release/tag, or deploy V2 production.
