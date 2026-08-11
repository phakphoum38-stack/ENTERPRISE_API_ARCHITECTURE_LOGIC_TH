from __future__ import annotations

import json
import os
import secrets
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from google_workspace import DEFAULT_SCOPES, GoogleWorkspaceConfig

AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
USERINFO_ENDPOINT = "https://openidconnect.googleapis.com/v1/userinfo"
IDENTITY_SCOPES = ("openid", "email", "profile")


class GoogleOAuthError(RuntimeError):
    pass


class GoogleOAuthBroker:
    def __init__(self, data_dir: str | os.PathLike[str] | None = None) -> None:
        self.config = GoogleWorkspaceConfig(data_dir)
        self.root = self.config.root
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_path = self.root / "oauth_state.json"
        self.token_path = self.root / "oauth_token.json"

    @property
    def client_id(self) -> str:
        return (os.environ.get("RESEARCH_OS_GOOGLE_CLIENT_ID") or os.environ.get("GOOGLE_CLIENT_ID") or "").strip()

    @property
    def client_secret(self) -> str:
        return (os.environ.get("RESEARCH_OS_GOOGLE_CLIENT_SECRET") or os.environ.get("GOOGLE_CLIENT_SECRET") or "").strip()

    def redirect_uri(self) -> str:
        explicit = (os.environ.get("RESEARCH_OS_GOOGLE_REDIRECT_URI") or "").strip()
        if explicit:
            return explicit
        port = int(os.environ.get("RESEARCH_OS_API_PORT", "8787"))
        return f"http://127.0.0.1:{port}/v1/google-workspace/oauth/callback"

    def _enabled_scopes(self) -> list[str]:
        enabled = self.config._load_enabled()
        scopes = set(IDENTITY_SCOPES)
        for service in enabled:
            scopes.update(DEFAULT_SCOPES.get(service, ()))
        return sorted(scopes)

    def begin(self) -> dict[str, Any]:
        if not self.config.oauth_configured:
            raise GoogleOAuthError("Google OAuth client ID/secret is not configured on the backend")
        state = secrets.token_urlsafe(32)
        payload = {
            "state": state,
            "created_at": int(time.time()),
            "redirect_uri": self.redirect_uri(),
        }
        self.state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri(),
            "response_type": "code",
            "scope": " ".join(self._enabled_scopes()),
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": state,
        }
        return {
            "authorization_url": f"{AUTH_ENDPOINT}?{urlencode(params)}",
            "redirect_uri": self.redirect_uri(),
            "state_created": True,
            "token_storage": "backend_only",
        }

    def _read_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            raise GoogleOAuthError("OAuth state is missing or expired")
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError) as exc:
            raise GoogleOAuthError("OAuth state is invalid") from exc

    def complete(self, *, code: str, state: str) -> dict[str, Any]:
        expected = self._read_state()
        created_at = int(expected.get("created_at", 0))
        if not secrets.compare_digest(str(expected.get("state", "")), state):
            raise GoogleOAuthError("OAuth state mismatch")
        if int(time.time()) - created_at > 600:
            raise GoogleOAuthError("OAuth state expired")
        body = urlencode(
            {
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri(),
                "grant_type": "authorization_code",
            }
        ).encode("utf-8")
        request = Request(TOKEN_ENDPOINT, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
        try:
            with urlopen(request, timeout=20) as response:
                token = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise GoogleOAuthError(f"Google token exchange failed: {exc}") from exc
        if not token.get("access_token"):
            raise GoogleOAuthError("Google token response did not include an access token")
        existing = self._read_token(silent=True)
        if not token.get("refresh_token") and existing.get("refresh_token"):
            token["refresh_token"] = existing["refresh_token"]
        token["obtained_at"] = int(time.time())
        token["redirect_uri"] = self.redirect_uri()
        self._write_token(token)
        self.state_path.unlink(missing_ok=True)
        account = self._fetch_userinfo(str(token["access_token"]))
        return {"connected": True, "account": account, "has_refresh_token": bool(token.get("refresh_token"))}

    def _write_token(self, payload: dict[str, Any]) -> None:
        self.token_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            os.chmod(self.token_path, 0o600)
        except OSError:
            pass

    def _read_token(self, *, silent: bool = False) -> dict[str, Any]:
        if not self.token_path.exists():
            return {} if silent else self._raise_not_connected()
        try:
            value = json.loads(self.token_path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, ValueError, TypeError):
            return {} if silent else self._raise_not_connected()

    @staticmethod
    def _raise_not_connected() -> dict[str, Any]:
        raise GoogleOAuthError("Google Workspace is not connected")

    def _fetch_userinfo(self, access_token: str) -> dict[str, Any]:
        request = Request(USERINFO_ENDPOINT, headers={"Authorization": f"Bearer {access_token}"})
        try:
            with urlopen(request, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return {}
        return {
            "email": payload.get("email"),
            "name": payload.get("name"),
            "picture": payload.get("picture"),
        }

    def status(self) -> dict[str, Any]:
        token = self._read_token(silent=True)
        connected = bool(token.get("access_token") or token.get("refresh_token"))
        local_account_accepted = self.config.local_account_accepted
        return {
            "oauth_configured": self.config.oauth_configured,
            "connected": connected,
            "app_access": connected or local_account_accepted,
            "local_account_accepted": local_account_accepted,
            "account_mode": "google" if connected else "local" if local_account_accepted else "none",
            "has_refresh_token": bool(token.get("refresh_token")),
            "redirect_uri": self.redirect_uri(),
            "token_storage": "backend_only",
        }

    def disconnect(self) -> dict[str, Any]:
        self.token_path.unlink(missing_ok=True)
        self.state_path.unlink(missing_ok=True)
        return {"connected": False, "disconnected": True}
