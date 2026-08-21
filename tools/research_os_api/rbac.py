from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable


class Role(str, Enum):
    USER = "USER"
    PRO = "PRO"
    OWNER = "OWNER"


class AuthorizationError(PermissionError):
    pass


@dataclass(frozen=True)
class Principal:
    email: str
    role: Role


ROLE_RANK = {Role.USER: 10, Role.PRO: 20, Role.OWNER: 30}


class RoleStore:
    """Small persistent role store keyed by verified Google email.

    The store never handles passwords or Google credentials. Owner/pro bootstrap
    lists come from environment variables; explicit persisted assignments are
    resource-neutral system roles only.
    """

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)
        self._lock = threading.RLock()
        self._roles: dict[str, Role] = {}
        self._load()

    @staticmethod
    def _normalize(email: str) -> str:
        value = email.strip().lower()
        if not value or "@" not in value or any(ch in value for ch in "\r\n\x00"):
            raise AuthorizationError("invalid account email")
        return value

    def _load(self) -> None:
        if not self.path.exists():
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return
        self._roles = {
            self._normalize(str(email)): Role(str(role).upper())
            for email, role in payload.get("roles", {}).items()
        }

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps({"roles": {email: role.value for email, role in sorted(self._roles.items())}}, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.path)

    @staticmethod
    def _env_emails(name: str) -> set[str]:
        raw = os.getenv(name, "")
        return {item.strip().lower() for item in raw.split(",") if item.strip()}

    def resolve(self, email: str) -> Principal:
        normalized = self._normalize(email)
        with self._lock:
            if normalized in self._roles:
                return Principal(normalized, self._roles[normalized])
        if normalized in self._env_emails("RESEARCH_OS_OWNER_EMAILS"):
            return Principal(normalized, Role.OWNER)
        if normalized in self._env_emails("RESEARCH_OS_PRO_EMAILS"):
            return Principal(normalized, Role.PRO)
        return Principal(normalized, Role.USER)

    def assign(self, actor: Principal, email: str, role: Role) -> Principal:
        if actor.role is not Role.OWNER:
            raise AuthorizationError("only OWNER may assign system roles")
        normalized = self._normalize(email)
        with self._lock:
            self._roles[normalized] = Role(role)
            self._save()
        return self.resolve(normalized)

    def require(self, principal: Principal, minimum: Role) -> None:
        if ROLE_RANK[principal.role] < ROLE_RANK[minimum]:
            raise AuthorizationError(
                f"{minimum.value} role required; {principal.role.value} is insufficient"
            )

    def snapshot(self, emails: Iterable[str]) -> dict[str, str]:
        return {email: self.resolve(email).role.value for email in emails}
