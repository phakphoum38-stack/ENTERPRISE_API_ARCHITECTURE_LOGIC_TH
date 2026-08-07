from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


WORKSPACE_SERVICES = (
    "drive",
    "docs",
    "sheets",
    "calendar",
    "gmail",
    "contacts",
    "tasks",
    "keep",
    "meet",
    "forms",
    "chat",
)

DEFAULT_SCOPES = {
    "drive": ("https://www.googleapis.com/auth/drive",),
    "docs": ("https://www.googleapis.com/auth/documents",),
    "sheets": ("https://www.googleapis.com/auth/spreadsheets",),
    "calendar": ("https://www.googleapis.com/auth/calendar",),
    "gmail": ("https://www.googleapis.com/auth/gmail.modify",),
    "contacts": ("https://www.googleapis.com/auth/contacts",),
    "tasks": ("https://www.googleapis.com/auth/tasks",),
    "keep": ("https://www.googleapis.com/auth/keep",),
    "meet": ("https://www.googleapis.com/auth/meetings.space.created",),
    "forms": ("https://www.googleapis.com/auth/forms.body.readonly", "https://www.googleapis.com/auth/forms.responses.readonly"),
    "chat": ("https://www.googleapis.com/auth/chat.spaces.readonly", "https://www.googleapis.com/auth/chat.messages.readonly"),
}


@dataclass(frozen=True)
class WorkspaceServiceStatus:
    service: str
    enabled: bool
    state: str
    scopes: tuple[str, ...]
    note: str = ""


class GoogleWorkspaceConfig:
    """Local-first Google Workspace configuration surface.

    Client secrets and refresh tokens stay on the backend. Flutter receives only
    capability/status metadata and never the raw credentials.
    """

    def __init__(self, data_dir: str | os.PathLike[str] | None = None) -> None:
        root = Path(data_dir or os.environ.get("RESEARCH_OS_DATA_DIR") or Path.home() / "ResearchOSData")
        self.root = root / "google_workspace"
        self.root.mkdir(parents=True, exist_ok=True)
        self.settings_path = self.root / "settings.json"
        self.token_path = self.root / "oauth_token.json"

    @property
    def client_id_configured(self) -> bool:
        return bool(os.environ.get("RESEARCH_OS_GOOGLE_CLIENT_ID") or os.environ.get("GOOGLE_CLIENT_ID"))

    @property
    def client_secret_configured(self) -> bool:
        return bool(os.environ.get("RESEARCH_OS_GOOGLE_CLIENT_SECRET") or os.environ.get("GOOGLE_CLIENT_SECRET"))

    @property
    def oauth_configured(self) -> bool:
        return self.client_id_configured and self.client_secret_configured

    @property
    def connected(self) -> bool:
        if not self.token_path.exists():
            return False
        try:
            payload = json.loads(self.token_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return False
        return bool(payload.get("access_token") or payload.get("refresh_token"))

    def _load_enabled(self) -> set[str]:
        if not self.settings_path.exists():
            return set(WORKSPACE_SERVICES)
        try:
            payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return set(WORKSPACE_SERVICES)
        raw = payload.get("enabled_services", WORKSPACE_SERVICES)
        return {str(item) for item in raw if str(item) in WORKSPACE_SERVICES}

    def set_enabled_services(self, services: Iterable[str]) -> None:
        enabled = sorted({str(item) for item in services if str(item) in WORKSPACE_SERVICES})
        self.settings_path.write_text(json.dumps({"enabled_services": enabled}, ensure_ascii=False, indent=2), encoding="utf-8")

    def statuses(self) -> list[WorkspaceServiceStatus]:
        enabled = self._load_enabled()
        result: list[WorkspaceServiceStatus] = []
        for service in WORKSPACE_SERVICES:
            is_enabled = service in enabled
            if not is_enabled:
                state = "disabled"
                note = "disabled by user"
            elif not self.oauth_configured:
                state = "not_configured"
                note = "Google OAuth client ID/secret required on backend"
            elif not self.connected:
                state = "ready_for_oauth"
                note = "OAuth credentials configured; user authorization still required"
            else:
                state = "connected"
                note = "Google OAuth token is stored on the backend"
            result.append(WorkspaceServiceStatus(service, is_enabled, state, DEFAULT_SCOPES[service], note))
        return result

    def dashboard(self) -> dict:
        statuses = self.statuses()
        return {
            "hub": "google_workspace",
            "oauth_configured": self.oauth_configured,
            "client_id_configured": self.client_id_configured,
            "client_secret_configured": self.client_secret_configured,
            "connected": self.connected,
            "services": [asdict(item) for item in statuses],
            "connected_count": sum(1 for item in statuses if item.state == "connected"),
            "enabled_count": sum(1 for item in statuses if item.enabled),
            "total_count": len(statuses),
            "token_storage": "backend_only",
            "local_root": str(self.root),
        }


def get_google_workspace_dashboard() -> dict:
    return GoogleWorkspaceConfig().dashboard()
