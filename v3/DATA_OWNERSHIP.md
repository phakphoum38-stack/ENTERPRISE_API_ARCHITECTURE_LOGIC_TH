# V3 Clean Data Ownership

V3 Clean has one explicit boundary for mutable local service data.

## Data root

The service resolves the root in this order:

1. `RESEARCH_OS_V3_DATA_DIR` when explicitly configured.
2. Windows: `%ProgramData%\ResearchOSV3`.
3. Other systems: `$XDG_DATA_HOME/research-os-v3` or `~/.local/share/research-os-v3`.

## User isolation

New user-owned mutable data is always scoped by a validated `UserContext`:

`users/<user-id>/profiles/<profile-id>/`

Each user/profile scope owns:

- `sessions/`
- `database/`
- `artifacts/`
- `logs/`
- `evidence/`

`user-id` and `profile-id` are restricted to safe path-component characters. Path traversal, slashes, backslashes, empty identifiers, `.` and `..` are rejected. The resolved scope is also checked to remain below the configured `users/` root.

The desktop app sends `X-Research-OS-User` and `X-Research-OS-Profile` to the local service. `/v3/user` requires a valid user context and returns only safe scope metadata; it does not return credentials.

## Compatibility directories

The pre-release V3 root-level `sessions/`, `database/`, `artifacts/`, `logs/`, and `evidence/` directories remain present during migration so previously validated installer/service behavior stays non-destructive. They are not the ownership location for new per-user application state. New user state must use `DataLayout.for_user(UserContext(...))`.

Legacy root data is never assigned automatically to a user. This avoids accidentally exposing previously shared data to the wrong profile.

## Lifecycle rules

- Initialization is idempotent: creating the layout again must not delete or overwrite existing data.
- User A and User B must resolve to different roots.
- Two profiles of the same user must resolve to different roots.
- Service stop/start must preserve all user scopes.
- In-place upgrades must preserve the complete data root and all user scopes.
- Normal uninstall must preserve the data root unless the user explicitly requests a data purge.
- Candidate validation must prove preservation before a release is marked passed.
- Source code, packaged runtime files, and installed binaries are not mutable user data and must not be stored in this root.

## Secret rule

Provider credentials are not owned by the data root. They come from a `SecretSource` (environment or Windows Credential Manager). API keys, bearer tokens, or raw credentials must never be serialized into sessions, database files, logs, artifacts, evidence, user scope metadata, or status contracts.
