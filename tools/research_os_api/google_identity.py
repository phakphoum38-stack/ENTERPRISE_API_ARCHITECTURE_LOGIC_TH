from __future__ import annotations

import os

from google_oauth import GoogleOAuthBroker, IDENTITY_SCOPES


class GoogleIdentityBroker(GoogleOAuthBroker):
    """Google identity sign-in using only OpenID email/profile scopes.

    This is intentionally separate from Google Workspace authorization so a
    Research OS sign-in never requests Drive, Gmail, Calendar, or other service
    permissions just to identify the user.
    """

    def __init__(self, data_dir: str | os.PathLike[str] | None = None) -> None:
        super().__init__(data_dir)
        self.state_path = self.root / "identity_oauth_state.json"
        self.token_path = self.root / "identity_oauth_token.json"

    def _enabled_scopes(self) -> list[str]:
        return sorted(IDENTITY_SCOPES)

    def redirect_uri(self) -> str:
        explicit = (
            os.environ.get("RESEARCH_OS_GOOGLE_IDENTITY_REDIRECT_URI") or ""
        ).strip()
        if explicit:
            return explicit
        port = int(os.environ.get("RESEARCH_OS_API_PORT", "8787"))
        return f"http://127.0.0.1:{port}/v1/auth/google/callback"
