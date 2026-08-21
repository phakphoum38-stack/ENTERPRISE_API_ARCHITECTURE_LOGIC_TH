from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


class ACLAuthorizationError(PermissionError):
    pass


@dataclass(frozen=True)
class FilePrincipal:
    email: str


class FileACLStore:
    """Resource-scoped file ownership and sharing policy.

    FILE_OWNER grants permissions only for the named resource. It never maps to
    the system OWNER role and therefore cannot escalate global administration.
    """

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)
        self._lock = threading.RLock()
        self._resources: dict[str, dict[str, object]] = {}
        self._load()

    @staticmethod
    def _email(email: str) -> str:
        value = email.strip().lower()
        if not value or "@" not in value or any(ch in value for ch in "\r\n\x00"):
            raise ACLAuthorizationError("invalid account email")
        return value

    @staticmethod
    def _resource(resource_id: str) -> str:
        value = resource_id.strip()
        if not value or len(value) > 256 or any(ch in value for ch in "\r\n\x00"):
            raise ACLAuthorizationError("invalid resource id")
        return value

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return
        if isinstance(payload, dict) and isinstance(payload.get("resources"), dict):
            self._resources = payload["resources"]

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps({"schema_version": 1, "resources": self._resources}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.path)

    def create(self, resource_id: str, owner_email: str) -> dict[str, object]:
        resource_id = self._resource(resource_id)
        owner_email = self._email(owner_email)
        with self._lock:
            item = self._resources.get(resource_id)
            if item is not None:
                if self._email(str(item.get("owner", ""))) != owner_email:
                    raise ACLAuthorizationError("resource already belongs to another owner")
                return dict(item)
            item = {"owner": owner_email, "collaborators": [], "history": [{"action": "created", "actor": owner_email}]}
            self._resources[resource_id] = item
            self._save()
            return dict(item)

    def _get(self, resource_id: str) -> dict[str, object]:
        item = self._resources.get(self._resource(resource_id))
        if item is None:
            raise ACLAuthorizationError("resource not found")
        return item

    def authorize(self, resource_id: str, actor_email: str, action: str) -> bool:
        actor_email = self._email(actor_email)
        action = action.strip().lower()
        if action not in {"read", "write", "delete", "share", "transfer"}:
            raise ACLAuthorizationError("unsupported resource action")
        item = self._get(resource_id)
        owner = self._email(str(item.get("owner", "")))
        collaborators = {self._email(str(v)) for v in item.get("collaborators", [])}
        if actor_email == owner:
            return True
        if action == "read":
            return actor_email in collaborators
        return False

    def share(self, resource_id: str, owner_email: str, collaborator_email: str) -> dict[str, object]:
        owner_email = self._email(owner_email)
        collaborator_email = self._email(collaborator_email)
        item = self._get(resource_id)
        if self._email(str(item.get("owner", ""))) != owner_email:
            raise ACLAuthorizationError("only FILE_OWNER may share this resource")
        collaborators = {self._email(str(v)) for v in item.get("collaborators", [])}
        collaborators.add(collaborator_email)
        item["collaborators"] = sorted(collaborators)
        item.setdefault("history", []).append({"action": "shared", "actor": owner_email, "target": collaborator_email})
        self._save()
        return dict(item)

    def revoke(self, resource_id: str, owner_email: str, collaborator_email: str) -> dict[str, object]:
        owner_email = self._email(owner_email)
        collaborator_email = self._email(collaborator_email)
        item = self._get(resource_id)
        if self._email(str(item.get("owner", ""))) != owner_email:
            raise ACLAuthorizationError("only FILE_OWNER may revoke this resource")
        collaborators = {self._email(str(v)) for v in item.get("collaborators", [])}
        collaborators.discard(collaborator_email)
        item["collaborators"] = sorted(collaborators)
        item.setdefault("history", []).append({"action": "revoked", "actor": owner_email, "target": collaborator_email})
        self._save()
        return dict(item)

    def transfer(self, resource_id: str, owner_email: str, new_owner_email: str) -> dict[str, object]:
        owner_email = self._email(owner_email)
        new_owner_email = self._email(new_owner_email)
        item = self._get(resource_id)
        if self._email(str(item.get("owner", ""))) != owner_email:
            raise ACLAuthorizationError("only FILE_OWNER may transfer this resource")
        item["owner"] = new_owner_email
        item.setdefault("history", []).append({"action": "transferred", "actor": owner_email, "target": new_owner_email})
        self._save()
        return dict(item)

    def snapshot(self, resource_id: str) -> dict[str, object]:
        return dict(self._get(resource_id))
