"""Provider-neutral login flow primitives for the Research OS identity boundary.

This module deliberately does not store provider secrets or tokens. It creates
short-lived OAuth state records and normalizes callback claims; concrete HTTP
routing can use these primitives without changing Friend or Calendar Tool
contracts.
"""
from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from typing import Any

from identity_providers import get_provider, normalize_account


STATE_TTL_SECONDS = 10 * 60


@dataclass(frozen=True)
class LoginState:
    provider: str
    state: str
    created_at: int
    redirect_uri: str

    def valid(self, now: int | None = None) -> bool:
        current = int(time.time()) if now is None else int(now)
        return current - self.created_at <= STATE_TTL_SECONDS


class MultiLoginError(RuntimeError):
    pass


def begin_login(provider: str, *, redirect_uri: str) -> tuple[LoginState, str]:
    identity_provider = get_provider(provider)
    if not identity_provider.available:
        raise MultiLoginError(f"identity provider is not configured: {identity_provider.name}")
    state = LoginState(
        provider=identity_provider.name,
        state=secrets.token_urlsafe(32),
        created_at=int(time.time()),
        redirect_uri=redirect_uri,
    )
    from urllib.parse import urlencode

    params = {
        "client_id": __import__("os").environ.get(identity_provider.client_id_env, ""),
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(identity_provider.scopes),
        "state": state.state,
    }
    if identity_provider.name == "google":
        params.update({"access_type": "offline", "prompt": "consent", "include_granted_scopes": "true"})
    return state, f"{identity_provider.authorization_endpoint}?{urlencode(params)}"


def normalize_callback(provider: str, payload: dict[str, Any]) -> dict[str, Any]:
    account = normalize_account(provider, payload)
    if not account.get("sub"):
        raise MultiLoginError("identity provider did not return a subject")
    if not account.get("email"):
        raise MultiLoginError("identity provider did not return an email")
    return {
        "provider": str(provider).strip().lower(),
        "sub": account["sub"],
        "email": account["email"],
        "name": account.get("name", ""),
        "picture": account.get("picture"),
        "login": account.get("login"),
    }
