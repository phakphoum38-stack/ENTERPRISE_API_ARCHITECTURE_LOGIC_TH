from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from google_workspace import DEFAULT_SCOPES, GoogleWorkspaceConfig

AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
USERINFO_ENDPOINT = "https://openidconnect.googleapis.com/v1/userinfo"
JWKS_ENDPOINT = "https://www.googleapis.com/oauth2/v3/certs"
IDENTITY_SCOPES = ("openid", "email", "profile")
OIDC_ISSUERS = {"https://accounts.google.com", "accounts.google.com"}
_STATE_TTL_SECONDS = 600
_JWKS_CACHE: dict[str, Any] = {"expires_at": 0, "keys": {}}
_SHA256_DIGEST_INFO_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")


class GoogleOAuthError(RuntimeError):
    pass


def _b64url_decode(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


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
        nonce = secrets.token_urlsafe(32)
        code_verifier = _b64url_encode(secrets.token_bytes(32))
        code_challenge = _b64url_encode(hashlib.sha256(code_verifier.encode("ascii")).digest())
        redirect_uri = self.redirect_uri()
        payload = {
            "state": state,
            "created_at": int(time.time()),
            "redirect_uri": redirect_uri,
            "nonce": nonce,
            "code_verifier": code_verifier,
        }
        self.state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self._enabled_scopes()),
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "nonce": nonce,
        }
        return {
            "authorization_url": f"{AUTH_ENDPOINT}?{urlencode(params)}",
            "redirect_uri": redirect_uri,
            "state": state,
            "state_created": True,
            "pkce": "S256",
            "nonce_created": True,
            "token_storage": "backend_only",
        }

    def _read_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            raise GoogleOAuthError("OAuth state is missing or expired")
        try:
            state = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError) as exc:
            raise GoogleOAuthError("OAuth state is invalid") from exc
        if not isinstance(state, dict):
            raise GoogleOAuthError("OAuth state is invalid")
        return state

    @staticmethod
    def _safe_google_error(exc: HTTPError) -> str:
        """Return Google's OAuth error without exposing request secrets or auth codes."""
        try:
            raw = exc.read().decode("utf-8", errors="replace")
            payload = json.loads(raw)
        except (OSError, UnicodeDecodeError, ValueError, TypeError):
            return f"http_{exc.code}"

        if isinstance(payload, dict):
            error = str(payload.get("error") or "").strip()
            description = str(payload.get("error_description") or "").strip()
            if error and description:
                return f"{error}: {description[:240]}"
            if error:
                return error
        return f"http_{exc.code}"

    @classmethod
    def _fetch_jwks(cls) -> dict[str, dict[str, int]]:
        request = Request(JWKS_ENDPOINT, headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
                cache_control = response.headers.get("Cache-Control", "")
        except Exception as exc:
            raise GoogleOAuthError("Google OIDC signing keys are unavailable") from exc
        keys: dict[str, dict[str, int]] = {}
        for item in payload.get("keys", []) if isinstance(payload, dict) else []:
            if item.get("kty") != "RSA" or item.get("alg") != "RS256" or not item.get("kid"):
                continue
            try:
                keys[str(item["kid"])] = {
                    "n": int.from_bytes(_b64url_decode(str(item["n"])), "big"),
                    "e": int.from_bytes(_b64url_decode(str(item["e"])), "big"),
                }
            except (ValueError, TypeError):
                continue
        if not keys:
            raise GoogleOAuthError("Google OIDC signing keys are invalid or empty")
        max_age = 3600
        for directive in cache_control.split(","):
            directive = directive.strip()
            if directive.startswith("max-age="):
                try:
                    max_age = max(60, min(int(directive.split("=", 1)[1]), 86400))
                except ValueError:
                    pass
        _JWKS_CACHE["keys"] = keys
        _JWKS_CACHE["expires_at"] = int(time.time()) + max_age
        return keys

    @classmethod
    def _jwks(cls) -> dict[str, dict[str, int]]:
        if int(time.time()) >= int(_JWKS_CACHE.get("expires_at", 0)):
            return cls._fetch_jwks()
        keys = _JWKS_CACHE.get("keys")
        if not isinstance(keys, dict) or not keys:
            return cls._fetch_jwks()
        return keys

    @classmethod
    def _verify_id_token(cls, id_token: str, *, nonce: str, client_id: str) -> dict[str, Any]:
        parts = id_token.split(".")
        if len(parts) != 3:
            raise GoogleOAuthError("Google ID token is malformed")
        try:
            header = json.loads(_b64url_decode(parts[0]).decode("utf-8"))
            claims = json.loads(_b64url_decode(parts[1]).decode("utf-8"))
            signature = _b64url_decode(parts[2])
        except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
            raise GoogleOAuthError("Google ID token is malformed") from exc
        if header.get("alg") != "RS256" or not header.get("kid"):
            raise GoogleOAuthError("Google ID token uses an unsupported signing algorithm")
        key = cls._jwks().get(str(header["kid"]))
        if key is None:
            _JWKS_CACHE["expires_at"] = 0
            key = cls._fetch_jwks().get(str(header["kid"]))
        if key is None:
            raise GoogleOAuthError("Google ID token signing key is unknown")
        signing_input = f"{parts[0]}.{parts[1]}".encode("ascii")
        digest = hashlib.sha256(signing_input).digest()
        expected_prefix = _SHA256_DIGEST_INFO_PREFIX + digest
        modulus_bytes = (key["n"].bit_length() + 7) // 8
        encoded = pow(int.from_bytes(signature, "big"), key["e"], key["n"]).to_bytes(modulus_bytes, "big")
        expected_padding = b"\x00\x01" + b"\xff" * (modulus_bytes - len(expected_prefix) - 3) + b"\x00" + expected_prefix
        if not secrets.compare_digest(encoded, expected_padding):
            raise GoogleOAuthError("Google ID token signature is invalid")

        issuer = str(claims.get("iss") or "")
        if issuer not in OIDC_ISSUERS:
            raise GoogleOAuthError("Google ID token issuer is invalid")
        audience = claims.get("aud")
        audiences = audience if isinstance(audience, list) else [audience]
        if client_id not in audiences:
            raise GoogleOAuthError("Google ID token audience is invalid")
        if isinstance(audience, list) and len(audience) > 1 and str(claims.get("azp") or "") != client_id:
            raise GoogleOAuthError("Google ID token authorized party is invalid")
        now = int(time.time())
        try:
            exp = int(claims["exp"])
        except (KeyError, TypeError, ValueError) as exc:
            raise GoogleOAuthError("Google ID token expiration is invalid") from exc
        if exp <= now:
            raise GoogleOAuthError("Google ID token expired")
        if int(claims.get("iat", now)) > now + 60:
            raise GoogleOAuthError("Google ID token issued-at time is invalid")
        if not secrets.compare_digest(str(claims.get("nonce") or ""), nonce):
            raise GoogleOAuthError("Google ID token nonce mismatch")
        if not str(claims.get("sub") or "").strip():
            raise GoogleOAuthError("Google ID token subject is missing")
        return claims

    def complete(self, *, code: str, state: str) -> dict[str, Any]:
        expected = self._read_state()
        created_at = int(expected.get("created_at", 0))
        expected_state = str(expected.get("state", ""))
        if not secrets.compare_digest(expected_state, state):
            raise GoogleOAuthError("OAuth state mismatch")
        if int(time.time()) - created_at > _STATE_TTL_SECONDS:
            self.state_path.unlink(missing_ok=True)
            raise GoogleOAuthError("OAuth state expired")
        redirect_uri = str(expected.get("redirect_uri") or "").strip()
        if not redirect_uri or redirect_uri != self.redirect_uri():
            raise GoogleOAuthError("OAuth redirect URI changed during login")
        nonce = str(expected.get("nonce") or "").strip()
        code_verifier = str(expected.get("code_verifier") or "").strip()
        if not nonce or not code_verifier:
            raise GoogleOAuthError("OAuth PKCE or nonce state is missing")
        # Consume state before exchanging the code so callback state is strictly one-time.
        self.state_path.unlink(missing_ok=True)
        body = urlencode(
            {
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
                "code_verifier": code_verifier,
            }
        ).encode("utf-8")
        request = Request(TOKEN_ENDPOINT, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
        try:
            with urlopen(request, timeout=20) as response:
                token = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = self._safe_google_error(exc)
            raise GoogleOAuthError(f"Google token exchange failed: {detail}") from exc
        except Exception as exc:
            raise GoogleOAuthError(f"Google token exchange failed: {type(exc).__name__}") from exc
        if not token.get("access_token"):
            raise GoogleOAuthError("Google token response did not include an access token")
        id_token = str(token.get("id_token") or "").strip()
        if not id_token:
            raise GoogleOAuthError("Google token response did not include an ID token")
        claims = self._verify_id_token(id_token, nonce=nonce, client_id=self.client_id)
        account = self._fetch_userinfo(str(token["access_token"]))
        if not account:
            account = {}
        account.setdefault("sub", claims.get("sub"))
        account.setdefault("email", claims.get("email"))
        account.setdefault("name", claims.get("name"))
        account.setdefault("picture", claims.get("picture"))
        if not str(account.get("sub") or "").strip() or not str(account.get("email") or "").strip():
            raise GoogleOAuthError("Google identity response is incomplete")
        existing = self._read_token(silent=True)
        if not token.get("refresh_token") and existing.get("refresh_token"):
            token["refresh_token"] = existing["refresh_token"]
        token.pop("id_token", None)
        token["obtained_at"] = int(time.time())
        token["redirect_uri"] = redirect_uri
        token["account"] = account
        token["oidc"] = {"issuer": str(claims.get("iss")), "subject": str(claims["sub"])}
        self._write_token(token)
        return {
            "connected": True,
            "account": account,
            "has_refresh_token": bool(token.get("refresh_token")),
            "redirect_uri": redirect_uri,
        }

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
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name"),
            "picture": payload.get("picture"),
            "email_verified": payload.get("email_verified"),
        }

    def status(self) -> dict[str, Any]:
        token = self._read_token(silent=True)
        connected = bool(token.get("access_token") or token.get("refresh_token"))
        account = token.get("account") if isinstance(token.get("account"), dict) else {}
        if connected and not account and token.get("access_token"):
            account = self._fetch_userinfo(str(token["access_token"]))
            if account:
                token["account"] = account
                self._write_token(token)
        return {
            "oauth_configured": self.config.oauth_configured,
            "connected": connected,
            "has_refresh_token": bool(token.get("refresh_token")),
            "redirect_uri": self.redirect_uri(),
            "token_storage": "backend_only",
            "account": account,
        }

    def disconnect(self) -> dict[str, Any]:
        self.token_path.unlink(missing_ok=True)
        self.state_path.unlink(missing_ok=True)
        return {"connected": False, "disconnected": True}
