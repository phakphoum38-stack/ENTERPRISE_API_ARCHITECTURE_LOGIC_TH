from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


class BrowserUseCloudError(Exception):
    """Raised when Browser Use Cloud cannot be reached or configured."""


class BrowserUseCloudConnector:
    """Backend-only Browser Use Cloud connector.

    The API key stays in the backend environment. The desktop app receives only
    safe session metadata; the CDP URL is stored locally because it grants
    browser-control access.
    """

    api_base = "https://api.browser-use.com"

    def __init__(
        self,
        data_dir: str | os.PathLike[str] | None = None,
        api_key: str | None = None,
    ) -> None:
        root = Path(data_dir or os.environ.get("RESEARCH_OS_DATA_DIR") or Path.home() / "ResearchOSData")
        self.root = root / "browser_use"
        self.root.mkdir(parents=True, exist_ok=True)
        self.session_path = self.root / "session.json"
        self.api_key = (api_key or os.environ.get("BROWSER_USE_API_KEY") or "").strip()

    @property
    def api_key_configured(self) -> bool:
        return bool(self.api_key)

    def status(self) -> dict[str, Any]:
        session = self._load_session()
        cdp_url = str(session.get("cdp_url") or "") if session else ""
        return {
            "provider": "browser_use_cloud",
            "api_key_configured": self.api_key_configured,
            "connected": bool(session.get("id")) if session else False,
            "browser_id": session.get("id") if session else None,
            "proxy_country_code": session.get("proxy_country_code") if session else None,
            "cdp_url_available": bool(cdp_url),
            "cdp_host": urllib.parse.urlsplit(cdp_url).hostname if cdp_url else None,
            "token_storage": "backend_env_only",
            "session_storage": "backend_local_only",
        }

    def connect(self, proxy_country_code: str = "us") -> dict[str, Any]:
        if not self.api_key_configured:
            raise BrowserUseCloudError("Set BROWSER_USE_API_KEY on the Research OS backend before connecting Browser Use Cloud.")

        proxy = (proxy_country_code or "us").strip().lower()[:2] or "us"
        payload = self._request("POST", "/api/v4/browsers", {"proxyCountryCode": proxy})
        browser_id = str(payload.get("id") or "").strip()
        cdp_url = str(payload.get("cdpUrl") or payload.get("cdp_url") or "").strip()
        if not browser_id or not cdp_url:
            raise BrowserUseCloudError("Browser Use Cloud did not return a browser id and CDP URL.")

        self.session_path.write_text(
            json.dumps(
                {
                    "id": browser_id,
                    "cdp_url": cdp_url,
                    "proxy_country_code": proxy,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return {**self.status(), "created": True}

    def disconnect(self) -> dict[str, Any]:
        session = self._load_session()
        browser_id = str(session.get("id") or "").strip() if session else ""
        if browser_id and self.api_key_configured:
            self._request("PATCH", f"/api/v4/browsers/{urllib.parse.quote(browser_id, safe='')}", {"action": "stop"})
        if self.session_path.exists():
            self.session_path.unlink()
        return {**self.status(), "stopped": bool(browser_id)}

    def _load_session(self) -> dict[str, Any]:
        if not self.session_path.exists():
            return {}
        try:
            payload = json.loads(self.session_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def _request(self, method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.api_base}{path}",
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Browser-Use-API-Key": self.api_key,
            },
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise BrowserUseCloudError(f"Browser Use Cloud HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise BrowserUseCloudError(f"Browser Use Cloud request failed: {exc.reason}") from exc

        try:
            decoded = json.loads(raw)
        except ValueError as exc:
            raise BrowserUseCloudError("Browser Use Cloud returned invalid JSON.") from exc
        if not isinstance(decoded, dict):
            raise BrowserUseCloudError("Browser Use Cloud returned an unexpected payload.")
        return decoded


def get_browser_use_status() -> dict[str, Any]:
    return BrowserUseCloudConnector().status()
