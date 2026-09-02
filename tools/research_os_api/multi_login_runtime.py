from __future__ import annotations

import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from auth_session import cookie_header, issue_session
from identity_providers import get_provider
from multi_login import normalize_callback

STATE_TTL_SECONDS = 600


class MultiLoginRuntimeError(ValueError):
    pass


@dataclass
class PendingLogin:
    provider: str
    state: str
    redirect_uri: str
    created_at: int


_PENDING: dict[str, PendingLogin] = {}


def begin_runtime_login(provider_name: str, redirect_uri: str) -> tuple[str, str]:
    provider = get_provider(provider_name)
    if not provider.available:
        raise MultiLoginRuntimeError(f"identity provider is unavailable: {provider_name}")
    state = secrets.token_urlsafe(32)
    _PENDING[state] = PendingLogin(provider.name, state, redirect_uri, int(time.time()))
    params = {"client_id": os.environ[provider.client_id_env], "redirect_uri": redirect_uri, "response_type": "code", "scope": " ".join(provider.scopes), "state": state}
    if provider.name == "google":
        params.update({"access_type": "offline", "prompt": "consent"})
    return state, provider.authorization_endpoint + "?" + urllib.parse.urlencode(params)


def _post_form(url: str, data: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode("utf-8"), headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        raise MultiLoginRuntimeError(f"identity token exchange failed: {exc}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        parsed = urllib.parse.parse_qs(raw)
        return {key: values[-1] for key, values in parsed.items()}


def _get_json(url: str, token: str) -> Any:
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json", "User-Agent": "Research-OS"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise MultiLoginRuntimeError(f"identity profile request failed: {exc}") from exc


def _github_verified_email(token: str) -> str | None:
    payload = _get_json("https://api.github.com/user/emails", token)
    if not isinstance(payload, list):
        return None
    verified = [item for item in payload if isinstance(item, dict) and item.get("verified") and item.get("email")]
    primary = next((item for item in verified if item.get("primary")), None)
    chosen = primary or (verified[0] if verified else None)
    return str(chosen.get("email")).strip() if chosen else None


def complete_runtime_login(code: str, state: str) -> dict[str, Any]:
    pending = _PENDING.pop(state, None)
    if pending is None or pending.created_at + STATE_TTL_SECONDS < int(time.time()):
        raise MultiLoginRuntimeError("login state is invalid or expired")
    provider = get_provider(pending.provider)
    token_payload = _post_form(provider.token_endpoint, {"client_id": os.environ[provider.client_id_env], "client_secret": os.environ[provider.client_secret_env], "code": code, "redirect_uri": pending.redirect_uri, "grant_type": "authorization_code"})
    access_token = str(token_payload.get("access_token") or "").strip()
    if not access_token:
        raise MultiLoginRuntimeError("identity provider did not return an access token")
    profile = _get_json(provider.userinfo_endpoint, access_token)
    if provider.name == "github" and isinstance(profile, dict) and not profile.get("email"):
        profile["email"] = _github_verified_email(access_token)
    principal = normalize_callback(provider.name, profile)
    principal["role"] = "USER"
    principal["user_id"] = f"{provider.name}:{principal['sub']}"
    session = issue_session(principal)
    return {"provider": provider.name, "principal": principal, "session": session, "set_cookie": cookie_header(session)}
