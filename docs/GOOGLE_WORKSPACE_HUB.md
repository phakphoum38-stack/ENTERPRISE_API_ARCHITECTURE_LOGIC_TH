# Research OS — Google Workspace Hub

## Goal

Google Workspace Hub is the single integration boundary between Research OS and Google services. Flutter never stores Google client secrets, refresh tokens, or service-account credentials. Authentication and API access live behind the Research OS backend.

## Supported service domains

| Service | Research OS purpose | Connector state |
|---|---|---|
| Google Drive | Files, folders, search, backup/sync | Core scaffold ready |
| Google Docs | Read/write document content, AI summaries | Core scaffold ready |
| Google Sheets | Rosters, tables, analysis, structured data | Core scaffold ready |
| Google Calendar | Events, shifts, schedules | Core scaffold ready |
| Gmail | Search/read/organize/send workflows | Core scaffold ready |
| Google Contacts / People | Contacts and directory projection | Core scaffold ready |
| Google Tasks | Task lists and to-do workflows | Core scaffold ready |
| Google Keep | Notes when supported by the account/API policy | Capability-gated |
| Google Meet | Meeting spaces and meeting metadata | Core scaffold ready |
| Google Forms | Form metadata and responses where scopes permit | Core scaffold ready |
| Google Chat | Spaces/messages where account/app policy permits | Capability-gated |

`Core scaffold ready` means the Research OS service registry, scope model, backend-only credential boundary, local configuration root, UI surface, and tests exist. It does **not** mean a Google account has already authorized the service.

## Authentication design

The backend reads these environment variables when Google OAuth is configured:

```text
RESEARCH_OS_GOOGLE_CLIENT_ID
RESEARCH_OS_GOOGLE_CLIENT_SECRET
```

Compatibility aliases may later support:

```text
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
```

Refresh/access tokens must never be compiled into Flutter or committed to Git. The durable implementation should use an OS-protected local credential store on Windows and a backend token broker for cloud deployments.

## Local-first storage

Workspace state is rooted under:

```text
%USERPROFILE%\ResearchOSData\google_workspace\
```

or under `RESEARCH_OS_DATA_DIR/google_workspace` when a custom data root is configured.

The settings file stores only non-secret preferences such as enabled services. Token material belongs in the future secure credential store and must not be written to `settings.json`.

## Service states

Each connector reports one of:

- `disabled` — user disabled the service.
- `not_configured` — OAuth client credentials are absent on the backend.
- `ready_for_oauth` — backend OAuth client is configured but the Google account has not authorized Research OS.
- `connected` — an authorized backend connection exists.
- `error` — reserved for runtime connector/auth failures.

## Permission model

Research OS requests scopes by service, not one unrestricted bundle. Users should only authorize services they need. The initial registry contains scope groups for Drive, Docs, Sheets, Calendar, Gmail, Contacts/People, Tasks, Keep, Meet, Forms, and Chat.

Some Google APIs have account-edition, administrator, app-verification, or domain-policy requirements. Research OS must capability-detect those services and show the real state instead of pretending the connector is available.

## AI and Memory integration

A connected Workspace source may contribute data to AI only through explicit connector operations. Persisting retrieved Google content into long-term Research OS Memory remains a separate explicit action and follows the Memory quality/review gate.

Planned flow:

```text
Google Workspace
      ↓
Workspace Connector
      ↓
Normalized Resource
      ├── Live AI context
      ├── Search result
      └── Explicit Memory Commit
```

## Implementation phases

### Phase 1 — Foundation (current)

- service registry
- per-service scopes
- local-first settings root
- backend-only secret boundary
- Google Workspace Hub UI
- unit tests

### Phase 2 — OAuth Broker

- authorization URL generation
- OAuth callback handler
- state/PKCE protection where applicable
- refresh-token lifecycle
- Windows protected token store
- disconnect/revoke

### Phase 3 — Connectors

- Drive
- Docs
- Sheets
- Calendar
- Gmail
- People/Contacts
- Tasks
- Meet
- Forms
- capability-gated Keep
- capability-gated Chat

### Phase 4 — Unified Workspace Search

- common result schema
- cross-service query
- source attribution
- pagination and rate-limit handling
- AI grounding

### Phase 5 — Automations and Sync

- user-selected sync policies
- delta/incremental synchronization where APIs support it
- backup/restore metadata
- connector health dashboard
- audit log

## Security invariants

1. No Google client secret or refresh token in Flutter.
2. No token material in Git.
3. Least-privilege scopes by service.
4. Explicit user authorization and disconnect.
5. Explicit Memory Commit for durable AI memory.
6. Connector failures must degrade independently; one Google service must not take down Research OS.
