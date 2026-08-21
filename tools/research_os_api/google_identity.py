from __future__ import annotations

import os

from google_oauth import GoogleOAuthBroker, IDENTITY_SCOPES
from rbac import RoleStore


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
        self.role_store = RoleStore(self.root / "roles.json")

    def _enabled_scopes(self) -> list[str]:
        return sorted(IDENTITY_SCOPES)

    def redirect_uri(self) -> str:
        explicit = (
            os.environ.get("RESEARCH_OS_GOOGLE_IDENTITY_REDIRECT_URI") or ""
        ).strip()
        if explicit:
            return explicit

        public_base = (
            os.environ.get("RESEARCH_OS_PUBLIC_BASE_URL")
            or os.environ.get("RENDER_EXTERNAL_URL")
            or ""
        ).strip().rstrip("/")
        if public_base:
            return f"{public_base}/v1/auth/google/callback"

        port = int(os.environ.get("RESEARCH_OS_API_PORT", "8787"))
        return f"http://127.0.0.1:{port}/v1/auth/google/callback"

    def _with_role(self, account: dict[str, object]) -> dict[str, object]:
        email = str(account.get("email") or "").strip()
        if not email:
            return account
        principal = self.role_store.resolve(email)
        return {**account, "role": principal.role.value}

    def complete(self, *, code: str, state: str) -> dict[str, object]:
        result = super().complete(code=code, state=state)
        account = result.get("account") if isinstance(result.get("account"), dict) else {}
        account = self._with_role(account)
        result["account"] = account
        return result

    def status(self) -> dict[str, object]:
        result = super().status()
        account = result.get("account") if isinstance(result.get("account"), dict) else {}
        result["account"] = self._with_role(account)
        return result
