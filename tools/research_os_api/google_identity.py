from __future__ import annotations

import inspect
import os
import threading
from http.server import BaseHTTPRequestHandler

from google_oauth import GoogleOAuthBroker, IDENTITY_SCOPES
from rbac import RoleStore
from auth_session import clear_cookie_header, revoke_session


_SIGNOUT_STATE = threading.local()
_SIGNOUT_HOOK_LOCK = threading.Lock()
_SIGNOUT_HOOK_INSTALLED = False


def _install_signout_cookie_hook() -> None:
    global _SIGNOUT_HOOK_INSTALLED
    if _SIGNOUT_HOOK_INSTALLED:
        return
    with _SIGNOUT_HOOK_LOCK:
        if _SIGNOUT_HOOK_INSTALLED:
            return
        original_send_response = BaseHTTPRequestHandler.send_response
        original_send_header = BaseHTTPRequestHandler.send_header

        def send_response(handler, code, message=None, _original=original_send_response):
            _original(handler, code, message)
            if getattr(_SIGNOUT_STATE, "pending", False):
                original_send_header(handler, "Set-Cookie", clear_cookie_header())
                _SIGNOUT_STATE.pending = False

        BaseHTTPRequestHandler.send_response = send_response
        _SIGNOUT_HOOK_INSTALLED = True


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
        """Disconnect Google identity and revoke the active Research OS session."""
        _install_signout_cookie_hook()
        _SIGNOUT_STATE.pending = True

        handler = None
        frame = inspect.currentframe()
        try:
            frame = frame.f_back if frame else None
            while frame:
                candidate = frame.f_locals.get("self")
                if (
                    candidate is not None
                    and candidate is not self
                    and hasattr(candidate, "headers")
                    and hasattr(candidate, "send_header")
                    and hasattr(candidate, "wfile")
                ):
                    handler = candidate
                    break
                frame = frame.f_back
        finally:
            del frame

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
                    pass

        return super().disconnect()
