# Research OS Identity v2

Research OS Identity v2 provides optional verified-email Owner Profiles without making sign-in mandatory.

## Behaviour

- No account: Research OS runs as General AI.
- Local email only: local profile convenience only; it grants no private-cloud access.
- Verified email: OTP verification creates a time-limited Owner Session.
- Owner Session tokens are stored by Flutter in `flutter_secure_storage`.
- Non-secret product preferences may sync between verified devices.
- Private Context is **not uploaded** by Identity v2.

## Cloud routes

The cloud `render_server.py` exposes:

- `POST /v1/identity/request-code`
- `POST /v1/identity/verify-code`
- `GET /v1/identity/profile`
- `POST /v1/identity/preferences`

Identity routes intentionally live on the cloud API so Local API auto-discovery does not change the user's account identity endpoint.

## Required server environment variables

Do not commit real values to GitHub.

```text
RESEARCH_OS_IDENTITY_SECRET=<random secret at least 32 characters>
RESEARCH_OS_SMTP_HOST=<smtp server hostname>
RESEARCH_OS_SMTP_PORT=587
RESEARCH_OS_SMTP_FROM=<sender email>
RESEARCH_OS_SMTP_USERNAME=<smtp login if required>
RESEARCH_OS_SMTP_PASSWORD=<smtp password/app password if required>
RESEARCH_OS_SMTP_SSL=0
```

Use `RESEARCH_OS_SMTP_SSL=1` for implicit TLS providers (commonly port 465). With the default `0`, the service connects with SMTP and upgrades using STARTTLS.

## Persistent profile storage

Identity state is written below:

```text
$RESEARCH_OS_DATA_DIR/identity/email_identity.json
```

If `RESEARCH_OS_DATA_DIR` is not set, the API uses `~/.research_os`.

On cloud hosts with ephemeral filesystems, configure a persistent disk and point `RESEARCH_OS_DATA_DIR` at that disk. Otherwise verified profiles/preferences can disappear after a redeploy or instance replacement.

## Security properties

- OTP codes expire after 10 minutes.
- A challenge allows at most 6 attempts.
- OTPs are stored only as HMAC hashes, never plaintext.
- Session tokens are HMAC signed and expire after 30 days.
- Email alone never authenticates a user.
- Session rejection (HTTP 401/403) clears the local verified session.
- Temporary network failure does not destroy a still-unexpired local session.
- Flutter provider/API secrets remain backend-only.

## What syncs in v2

Only this allow-list can be stored in the cloud Owner Profile:

```text
theme
language
api_auto_discovery
api_scan_lan
heartbeat_seconds
```

The Flutter implementation currently synchronizes the API connection preferences. Additional non-sensitive settings can be added later through the same allow-list.

## What does NOT sync

Identity v2 deliberately does not upload:

- `private_context.md`
- personal project memory
- relationship/feeling context
- provider API keys
- GitHub tokens
- Google tokens
- arbitrary conversation history

Private Context remains local until a separate end-to-end encrypted Private Sync layer is implemented.

## Recommended deployment order

1. Set a persistent `RESEARCH_OS_DATA_DIR` on the cloud service.
2. Generate and set `RESEARCH_OS_IDENTITY_SECRET`.
3. Configure SMTP environment variables.
4. Restart the cloud service.
5. Test `request-code` using a non-sensitive test account.
6. Verify the six-digit code in Research OS Settings.
7. Confirm the UI shows `Verified Owner`.
8. Open Research OS on another device and verify the same email there.
9. Confirm API Manager preferences are restored after verification.

No GitHub workflow changes are required for Identity v2.
