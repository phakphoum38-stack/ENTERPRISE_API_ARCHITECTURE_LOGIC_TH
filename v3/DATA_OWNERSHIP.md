# V3 Clean Data Ownership

V3 Clean has one explicit boundary for mutable local service data.

## Data root

The service resolves the root in this order:

1. `RESEARCH_OS_V3_DATA_DIR` when explicitly configured.
2. Windows: `%ProgramData%\ResearchOSV3`.
3. Other systems: `$XDG_DATA_HOME/research-os-v3` or `~/.local/share/research-os-v3`.

## Owned directories

- `sessions/` - conversation/session state owned by V3.
- `database/` - durable structured state and indexes.
- `artifacts/` - generated durable artifacts intended to survive process restarts.
- `logs/` - service/application diagnostics. Logs must not contain provider secrets.
- `evidence/` - durable validation/evidence records when persisted locally.

## Lifecycle rules

- Initialization is idempotent: creating the layout again must not delete or overwrite existing user data.
- Service stop/start must preserve the complete data root.
- In-place upgrades must preserve the complete data root.
- Normal uninstall must preserve the data root unless the user explicitly requests a data purge.
- Candidate validation must prove preservation before a release is marked passed.
- Source code, packaged runtime files, and installed binaries are not mutable user data and must not be stored in this root.

## Secret rule

Provider credentials are not owned by the data root. They come from a `SecretSource` (environment today; OS-native secret storage later). API keys, bearer tokens, or raw credentials must never be serialized into sessions, database files, logs, artifacts, evidence, or status contracts.
