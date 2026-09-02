from __future__ import annotations

from http.cookies import SimpleCookie
from urllib.parse import parse_qs, urlparse

from auth_session import SESSION_COOKIE, clear_cookie_header, revoke_session, verify_session
from multi_login_runtime import MultiLoginRuntimeError, begin_runtime_login, complete_runtime_login


def _session_token(cookie_header_value: str | None) -> str:
    if not cookie_header_value:
        return ""
    cookie = SimpleCookie()
    try:
        cookie.load(cookie_header_value)
    except (CookieError, ValueError):
        return ""
    morsel = cookie.get(SESSION_COOKIE)
    return morsel.value if morsel is not None else ""


def auth_provider_login(provider: str, redirect_uri: str) -> dict:
    _, authorization_url = begin_runtime_login(provider, redirect_uri)
    return {"authorization_url": authorization_url, "redirect_uri": redirect_uri, "token_storage": "backend_only"}


def auth_callback(provider: str, query: str) -> tuple[dict, str]:
    values = parse_qs(urlparse("?" + query).query)
    error = values.get("error", [None])[0]
    if error:
        raise MultiLoginRuntimeError(f"identity provider returned error: {error}")
    code = values.get("code", [None])[0]
    state = values.get("state", [None])[0]
    if not code or not state:
        raise MultiLoginRuntimeError("OAuth callback requires code and state")
    result = complete_runtime_login(code, state)
    return result, result["set_cookie"]


def auth_status(cookie_header_value: str | None) -> dict:
    token = _session_token(cookie_header_value)
    if not token:
        return {"connected": False, "account": None}
    try:
        session = verify_session(token)
    except ValueError:
        return {"connected": False, "account": None}
    return {"connected": True, "account": {"user_id": session["user_id"], "email": session["email"], "role": session["role"]}}


def auth_signout(cookie_header_value: str | None) -> str:
    token = _session_token(cookie_header_value)
    if token:
        try:
            revoke_session(token)
        except ValueError:
            pass
    return clear_cookie_header()
