# Research OS Desktop Google OAuth Handoff

## Contract

The Research OS desktop client starts Google identity OAuth in the system browser. The browser receives the normal Google callback on the Research OS API, where the backend issues the signed Research OS session and keeps the session out of the browser redirect URL.

For a native client, the OAuth `state` is also registered as a short-lived (120 second), single-use handoff key. The backend stores the signed session behind that key. A native client can present the state through `X-Research-OS-OAuth-State`; the API authentication guard resolves the key to the signed session and consumes it exactly once.

## Security properties

- Google identity uses only `openid`, `email`, and `profile` scopes.
- Google Workspace credentials and tokens remain separate from Research OS identity.
- Calendar is not part of Research OS authentication.
- The signed Research OS session is never placed in the OAuth callback URL.
- Handoff keys expire after 120 seconds and are single-use.
- Handoff storage is backend-local and intended only for the short transition window; long-lived client session persistence is a separate secure-storage phase.
- Invalid or missing handoff state fails closed.

## Next client phase

1. Parse OAuth `state` from the authorization URL.
2. Poll the auth status endpoint while the browser completes sign-in.
3. Once authenticated, persist the signed session in platform secure storage.
4. Attach `X-Research-OS-Session` to API calls.
5. Clear the local session on sign-out or invalid-session response.

The implementation deliberately separates the browser OAuth exchange from native session persistence so one platform's callback mechanism does not become a dependency of another platform.
