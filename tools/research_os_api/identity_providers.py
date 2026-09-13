from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IdentityProvider:
    """OIDC/OAuth identity-provider metadata; secrets stay in environment/config."""

    name: str
    display_name: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    scopes: tuple[str, ...]
    client_id_env: str
    client_secret_env: str
    enabled_env: str

    @property
    def configured(self) -> bool:
        return bool(os.getenv(self.client_id_env) and os.getenv(self.client_secret_env))

    @property
    def enabled(self) -> bool:
        raw = os.getenv(self.enabled_env, "true").strip().lower()
        return raw not in {"0", "false", "no", "off"}

    @property
    def available(self) -> bool:
        return self.enabled and self.configured


IDENTITY_PROVIDERS: dict[str, IdentityProvider] = {
    "google": IdentityProvider(
        name="google",
        display_name="Google",
        authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
        token_endpoint="https://oauth2.googleapis.com/token",
        userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
        scopes=("openid", "email", "profile"),
        client_id_env="RESEARCH_OS_GOOGLE_CLIENT_ID",
        client_secret_env="RESEARCH_OS_GOOGLE_CLIENT_SECRET",
        enabled_env="RESEARCH_OS_LOGIN_GOOGLE_ENABLED",
    ),
    "microsoft": IdentityProvider(
        name="microsoft",
        display_name="Microsoft",
        authorization_endpoint="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        token_endpoint="https://login.microsoftonline.com/common/oauth2/v2.0/token",
        userinfo_endpoint="https://graph.microsoft.com/oidc/userinfo",
        scopes=("openid", "email", "profile", "User.Read"),
        client_id_env="RESEARCH_OS_MICROSOFT_CLIENT_ID",
        client_secret_env="RESEARCH_OS_MICROSOFT_CLIENT_SECRET",
        enabled_env="RESEARCH_OS_LOGIN_MICROSOFT_ENABLED",
    ),
    "github": IdentityProvider(
        name="github",
        display_name="GitHub",
        authorization_endpoint="https://github.com/login/oauth/authorize",
        token_endpoint="https://github.com/login/oauth/access_token",
        userinfo_endpoint="https://api.github.com/user",
        scopes=("read:user", "user:email"),
        client_id_env="RESEARCH_OS_GITHUB_CLIENT_ID",
        client_secret_env="RESEARCH_OS_GITHUB_CLIENT_SECRET",
        enabled_env="RESEARCH_OS_LOGIN_GITHUB_ENABLED",
    ),
}


def get_provider(name: str) -> IdentityProvider:
    key = str(name or "").strip().lower()
    try:
        return IDENTITY_PROVIDERS[key]
    except KeyError as exc:
        raise ValueError(f"unsupported identity provider: {key}") from exc


def provider_catalog() -> list[dict[str, Any]]:
    return [
        {
            "id": provider.name,
            "name": provider.display_name,
            "enabled": provider.enabled,
            "configured": provider.configured,
            "available": provider.available,
            "scopes": list(provider.scopes),
        }
        for provider in IDENTITY_PROVIDERS.values()
    ]


def normalize_account(provider: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Map provider-specific identity claims to the Research OS principal shape."""
    name = str(provider or "").strip().lower()
    if name == "github":
        subject = str(payload.get("id") or payload.get("node_id") or "").strip()
        email = str(payload.get("email") or "").strip().lower()
        display_name = str(payload.get("name") or payload.get("login") or "").strip()
        return {"sub": subject, "email": email, "name": display_name, "login": payload.get("login")}

    subject = str(payload.get("sub") or payload.get("id") or "").strip()
    email = str(payload.get("email") or payload.get("preferred_username") or "").strip().lower()
    display_name = str(payload.get("name") or payload.get("given_name") or "").strip()
    return {"sub": subject, "email": email, "name": display_name, "picture": payload.get("picture")}
