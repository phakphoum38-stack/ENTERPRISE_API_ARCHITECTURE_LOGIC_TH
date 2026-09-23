from __future__ import annotations

from http.cookies import CookieError, SimpleCookie
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from auth_session import SESSION_COOKIE, clear_cookie_header, cookie_header, revoke_session, verify_session
from google_identity import GoogleIdentityBroker
from multi_login_runtime import MultiLoginRuntimeError, begin_runtime_login, complete_runtime_login
from oauth_handoff import consume_handoff, create_handoff


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
    session = str(result.get("session") or "").strip()
    if not session:
        raise MultiLoginRuntimeError("identity provider login did not produce a Research OS session")
    # Keep the signed session out of the browser redirect URL.
    # Reuse OAuth state as a short-lived, single-use native-client handoff key.
    create_handoff(Path(__file__).resolve().parents[2], session, "", code=state)
    return result, result["set_cookie"]


def google_auth_callback(query: str) -> tuple[dict, str]:
    """Complete Google identity OAuth and return the canonical session cookie."""
    values = parse_qs(urlparse("?" + query).query)
    error = str(values.get("error", [""])[0]).strip()
    if error:
        raise MultiLoginRuntimeError(f"identity provider returned error: {error}")
    code = str(values.get("code", [""])[0]).strip()
    state = str(values.get("state", [""])[0]).strip()
    if not code or not state:
        raise MultiLoginRuntimeError("Google OAuth callback requires code and state")

    result = GoogleIdentityBroker().complete(code=code, state=state)
    session = str(result.get("session") or "").strip()
    if not session:
        raise MultiLoginRuntimeError("Google OAuth completion did not produce a Research OS session")
    account = result.get("account") if isinstance(result.get("account"), dict) else {}
    return {"provider": "google", "account": account, "session": session}, cookie_header(session, secure=True)


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

def auth_provider_handoff(state: str) -> dict:
    handoff = str(state or "").strip()
    if not handoff:
        raise MultiLoginRuntimeError("OAuth handoff state is required")
    session = consume_handoff(Path(__file__).resolve().parents[2], handoff)
    if not session:
        raise MultiLoginRuntimeError("OAuth handoff is missing, expired, or already consumed")
    principal = verify_session(session)
    return {"connected": True, "session": session, "account": {"user_id": principal["user_id"], "email": principal["email"], "role": principal["role"]}, "token_type": "research_os_session"}
