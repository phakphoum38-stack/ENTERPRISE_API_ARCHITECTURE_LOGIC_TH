from __future__ import annotations

import inspect
import os

from google_oauth import GoogleOAuthBroker, IDENTITY_SCOPES
from rbac import RoleStore
from auth_session import clear_cookie_header, revoke_session


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

    def disconnect(self) -> dict[str, object]:
        """Disconnect Google identity and revoke the active Research OS session.

        The HTTP handler invokes this method while processing the signout
        request. The handler is discovered from the active call frame so the
        signed session presented by the client is revoked before the response
        is emitted. The response path is also wrapped once to emit the
        canonical session-clearing cookie header.
        """
        handler = None
        for frame_info in inspect.stack(context=0):
            candidate = frame_info.frame.f_locals.get("self")
            if candidate is not self and hasattr(candidate, "headers") and hasattr(candidate, "send_header"):
                handler = candidate
                break

        if handler is not None:
            token = handler.headers.get("X-Research-OS-Session")
            if not token:
                cookie = handler.headers.get("Cookie", "")
                marker = "research_os_session="
                for part in cookie.split(";"):
                    part = part.strip()
                    if part.startswith(marker):
                        token = part[len(marker):]
                        break

            if token:
                try:
                    revoke_session(token)
                except ValueError:
                    # Signout must still clear the browser cookie when the
                    # presented session is already invalid.
                    pass

            original_send_header = handler.send_header
            injected = False

            def send_header(name: str, value: str, _original=original_send_header):
                nonlocal injected
                if not injected:
                    _original("Set-Cookie", clear_cookie_header())
                    injected = True
                _original(name, value)

            handler.send_header = send_header

        return super().disconnect()
