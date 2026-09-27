"""Durable management-plane registry and service for Research OS APIs.

This module owns metadata/lifecycle only. Runtime authorization, quota, budget,
admission, routing, usage accounting, and evidence remain canonical elsewhere.
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
from dataclasses import asdict, fields, replace
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Type

from tools.research_os_api.api_key_store import JsonAPIKeyStore
from tools.research_os_api.api_keys import APIKeyManager
from tools.research_os_api.api_management_models import (
    API, APIEndpoint, APIKey, APIVersion, APIProduct, Application,
    DeveloperPortalMetadata, Entitlement, GatewayRoute, Lifecycle, Organization,
    Plan, Project, Scope, Webhook,
)
from tools.research_os_api.api_platform.api_management_registry import ManagementRegistry

RESOURCE_TYPES: dict[str, Type[Any]] = {
    "organizations": Organization,
    "projects": Project,
    "applications": Application,
    "apis": API,
    "versions": APIVersion,
    "endpoints": APIEndpoint,
    "scopes": Scope,
    "api_keys": APIKey,
    "plans": Plan,
    "entitlements": Entitlement,
    "routes": GatewayRoute,
    "webhooks": Webhook,
    "products": APIProduct,
    "portals": DeveloperPortalMetadata,
}
ID_FIELDS = {
    "organizations": "organization_id", "projects": "project_id",
    "applications": "application_id", "apis": "api_id", "versions": "version_id",
    "endpoints": "endpoint_id", "scopes": "scope_id", "api_keys": "key_id",
    "plans": "plan_id", "entitlements": "entitlement_id", "routes": "route_id",
    "webhooks": "webhook_id", "products": "product_id", "portals": "project_id",
}
TUPLE_FIELDS = {
    "endpoints": {"scopes"}, "api_keys": {"scopes"}, "entitlements": {"scope_ids", "policy_ids"},
    "plans": {"entitlement_ids"}, "webhooks": {"event_types"}, "products": {"api_ids", "plan_ids"},
    "portals": {"sdk_languages"},
}
DATETIME_FIELDS = {"api_keys": {"created_at", "expires_at", "revoked_at"}}
RELATION_ORDER = ("organizations", "projects", "applications", "apis", "versions",
                  "scopes", "endpoints", "plans", "entitlements", "api_keys",
                  "routes", "webhooks", "products", "portals")


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if hasattr(value, "__dataclass_fields__"):
        return {k: _jsonable(v) for k, v in asdict(value).items()}
    return value


def _decode(resource: str, payload: dict[str, Any]) -> Any:
    cls = RESOURCE_TYPES[resource]
    data = dict(payload)
    for name in TUPLE_FIELDS.get(resource, set()):
        if name in data:
            data[name] = tuple(data[name] or ())
    for name in DATETIME_FIELDS.get(resource, set()):
        value = data.get(name)
        data[name] = datetime.fromisoformat(value) if isinstance(value, str) and value else None
    if cls in (API, Plan) and isinstance(data.get("lifecycle"), str):
        data["lifecycle"] = Lifecycle(data["lifecycle"])
    return cls(**{field.name: data[field.name] for field in fields(cls) if field.name in data})


class JsonManagementStore:
    """Atomic JSON persistence for management metadata; secrets are never stored here."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        if not self.path.exists():
            self._write({"resources": {resource: {} for resource in RESOURCE_TYPES}, "audit": []})

    def _read(self) -> dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            raise RuntimeError("management store is unavailable or corrupt") from exc

    def _write(self, value: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(prefix=self.path.name + ".", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, self.path)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return self._read()

    def put(self, resource: str, identifier: str, payload: dict[str, Any]) -> None:
        with self._lock:
            state = self._read()
            state["resources"].setdefault(resource, {})[identifier] = _jsonable(payload)
            self._write(state)

    def list(self, resource: str) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._read()["resources"].get(resource, {}).values())

    def get(self, resource: str, identifier: str) -> dict[str, Any] | None:
        with self._lock:
            return self._read()["resources"].get(resource, {}).get(identifier)

    def record_audit(self, actor: str, resource: str, identifier: str, action: str, outcome: str) -> None:
        with self._lock:
            state = self._read()
            state.setdefault("audit", []).append({
                "actor": actor, "resource": resource, "identifier": identifier,
                "action": action, "outcome": outcome, "timestamp": datetime.utcnow().isoformat() + "Z",
            })
            self._write(state)

    def audit(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._read().get("audit", []))


class ManagementService:
    """CRUD/lifecycle facade over the canonical management registry."""

    def __init__(self, store: JsonManagementStore) -> None:
        self.store = store
        self.registry = ManagementRegistry()
        self._load()
        key_path = Path(os.getenv("RESEARCH_OS_API_KEY_STORE", str(self.store.path.with_name("api_keys.json"))))
        self.key_manager = APIKeyManager(JsonAPIKeyStore(key_path))

    @classmethod
    def from_env(cls) -> "ManagementService":
        root = Path(os.getenv("RESEARCH_OS_API_MANAGEMENT_DATA_DIR", "research/data/api_management"))
        return cls(JsonManagementStore(root / "management.json"))

    def _load(self) -> None:
        state = self.store.snapshot().get("resources", {})
        for resource in RELATION_ORDER:
            for payload in state.get(resource, {}).values():
                self._add_typed(resource, _decode(resource, payload))

    def _add_typed(self, resource: str, obj: Any) -> Any:
        method = {
            "organizations": "add_organization", "projects": "add_project",
            "applications": "add_application", "apis": "add_api", "versions": "add_version",
            "endpoints": "add_endpoint", "scopes": "add_scope", "plans": "add_plan",
            "entitlements": "add_entitlement", "routes": "add_route", "webhooks": "add_webhook",
            "products": "add_product", "portals": "set_portal",
        }.get(resource)
        if method is None:
            raise ValueError(f"unsupported management resource: {resource}")
        if resource == "api_keys":
            return self.registry.add_api_key(obj, entitlement_scope_ids=obj.scopes)
        return getattr(self.registry, method)(obj)

    def _persist(self, resource: str, obj: Any, *, actor: str, action: str) -> dict[str, Any]:
        identifier = getattr(obj, ID_FIELDS[resource])
        payload = _jsonable(asdict(obj))
        self.store.put(resource, identifier, payload)
        self.store.record_audit(actor, resource, identifier, action, "success")
        return payload

    def create_api_key(self, payload: dict[str, Any], *, actor: str = "system") -> dict[str, Any]:
        application_id = str(payload.get("application_id", "")).strip()
        principal_id = str(payload.get("principal_id", "")).strip()
        scopes = frozenset(str(value) for value in payload.get("scopes", []))
        if not application_id or not principal_id:
            raise ValueError("application_id and principal_id are required")
        application = _decode("applications", self.get("applications", application_id))
        if application.application_id != application_id:
            raise ValueError("application mismatch")
        raw = payload.get("raw_secret")
        if raw is not None:
            raise ValueError("raw_secret is server-generated")
        expires = payload.get("expires_at")
        expires_at = datetime.fromisoformat(expires) if isinstance(expires, str) and expires else None
        record, secret = self.key_manager.create(principal_id, set(scopes), expires_at=expires_at)
        obj = APIKey(record.key_id, application_id, record.fingerprint, tuple(sorted(scopes)), record.created_at, record.expires_at, record.revoked_at)
        self._add_typed("api_keys", obj)
        result = self._persist("api_keys", obj, actor=actor, action="create")
        result["raw_secret"] = secret
        return result

    def revoke_api_key(self, key_id: str, *, actor: str = "system") -> dict[str, Any]:
        record = self.key_manager.revoke(key_id)
        current = _decode("api_keys", self.get("api_keys", key_id))
        updated = replace(current, revoked_at=record.revoked_at)
        self._replace_and_validate("api_keys", key_id, updated)
        result = self._persist("api_keys", updated, actor=actor, action="revoke")
        return result

    def rotate_api_key(self, key_id: str, payload: dict[str, Any], *, actor: str = "system") -> dict[str, Any]:
        current = _decode("api_keys", self.get("api_keys", key_id))
        scopes = frozenset(str(value) for value in payload.get("scopes", current.scopes))
        expires = payload.get("expires_at")
        expires_at = datetime.fromisoformat(expires) if isinstance(expires, str) and expires else None
        record, secret = self.key_manager.rotate(key_id, str(payload.get("principal_id") or current.application_id), set(scopes), expires_at=expires_at)
        old = replace(current, revoked_at=record.created_at)
        self._replace_and_validate("api_keys", key_id, old)
        self._persist("api_keys", old, actor=actor, action="rotate_revoke")
        replacement = APIKey(record.key_id, current.application_id, record.fingerprint, tuple(sorted(scopes)), record.created_at, record.expires_at, record.revoked_at)
        self._add_typed("api_keys", replacement)
        result = self._persist("api_keys", replacement, actor=actor, action="rotate_create")
        result["raw_secret"] = secret
        return result
    def create(self, resource: str, payload: dict[str, Any], *, actor: str = "system") -> dict[str, Any]:
        if resource not in RESOURCE_TYPES:
            raise ValueError("unknown management resource")
        if resource == "api_keys":
            raise ValueError("API keys require the credential lifecycle service")
        obj = _decode(resource, payload)
        self._add_typed(resource, obj)
        return self._persist(resource, obj, actor=actor, action="create")

    def list(self, resource: str) -> list[dict[str, Any]]:
        if resource not in RESOURCE_TYPES:
            raise ValueError("unknown management resource")
        return self.store.list(resource)

    def get(self, resource: str, identifier: str) -> dict[str, Any]:
        value = self.store.get(resource, identifier)
        if value is None:
            raise KeyError(f"management object not found: {resource}/{identifier}")
        return value

    def update(self, resource: str, identifier: str, changes: dict[str, Any], *, actor: str = "system") -> dict[str, Any]:
        current = _decode(resource, self.get(resource, identifier))
        allowed = {field.name for field in fields(current)}
        unknown = sorted(set(changes) - allowed)
        if unknown:
            raise ValueError("unknown fields: " + ", ".join(unknown))
        candidate_data = _jsonable(asdict(current))
        candidate_data.update(changes)
        candidate = _decode(resource, candidate_data)
        self._replace_and_validate(resource, identifier, candidate)
        return self._persist(resource, candidate, actor=actor, action="update")

    def lifecycle(self, resource: str, identifier: str, action: str, *, actor: str = "system") -> dict[str, Any]:
        current = _decode(resource, self.get(resource, identifier))
        if resource not in {"apis", "plans", "products", "routes", "webhooks", "versions"}:
            raise ValueError("lifecycle action is not supported for this resource")
        if resource == "routes" or resource == "webhooks":
            enabled = action == "enable"
            candidate = replace(current, enabled=enabled)
        elif resource == "versions":
            candidate = replace(current, released=action == "release")
        else:
            lifecycle = Lifecycle.ACTIVE if action in {"publish", "enable", "release"} else Lifecycle.DISABLED
            candidate = replace(current, lifecycle=lifecycle)
        self._replace_and_validate(resource, identifier, candidate)
        return self._persist(resource, candidate, actor=actor, action=action)

    def _replace_and_validate(self, resource: str, identifier: str, candidate: Any) -> None:
        original = self.store.get(resource, identifier)
        if original is None:
            raise KeyError(identifier)
        setattr(self.registry, resource, dict(getattr(self.registry, resource)))
        getattr(self.registry, resource)[identifier] = candidate
        try:
            rebuilt = ManagementRegistry()
            for name in RELATION_ORDER:
                values = dict(getattr(self.registry, name))
                for key, obj in values.items():
                    if name == resource and key == identifier:
                        obj = candidate
                    if name == "api_keys":
                        rebuilt.add_api_key(obj, entitlement_scope_ids=obj.scopes)
                    elif name == "portals":
                        rebuilt.set_portal(obj)
                    else:
                        method = {
                            "organizations": "add_organization", "projects": "add_project",
                            "applications": "add_application", "apis": "add_api", "versions": "add_version",
                            "endpoints": "add_endpoint", "scopes": "add_scope", "plans": "add_plan",
                            "entitlements": "add_entitlement", "routes": "add_route",
                            "webhooks": "add_webhook", "products": "add_product",
                        }[name]
                        getattr(rebuilt, method)(obj)
        except Exception:
            self._load()
            raise
        self.registry = rebuilt
        self.store.put(resource, identifier, _jsonable(asdict(candidate)))


def default_management_service() -> ManagementService:
    return ManagementService.from_env()
