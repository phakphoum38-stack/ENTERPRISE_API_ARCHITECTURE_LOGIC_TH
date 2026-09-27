"""HTTP adapter for the API Management Platform.

The adapter is intentionally thin: authentication is delegated to the canonical
Research OS session verifier and execution authority remains the runtime control
plane. This module only maps HTTP requests to management metadata operations.
"""
from __future__ import annotations

from dataclasses import asdict
import json
from typing import Any, Callable
from urllib.parse import parse_qs, urlsplit

from tools.research_os_api.api_platform.management_service import ManagementService

RESOURCE_BY_SEGMENT = {
    "organizations": "organizations", "projects": "projects", "applications": "applications",
    "apis": "apis", "versions": "versions", "endpoints": "endpoints", "scopes": "scopes",
    "plans": "plans", "entitlements": "entitlements", "products": "products",
    "routes": "routes", "webhooks": "webhooks",
}
STATUS = {"GET": 200, "POST": 201, "PATCH": 200}


class ManagementHTTP:
    def __init__(self, service: ManagementService, authenticate: Callable[[Any], dict[str, Any] | None]) -> None:
        self.service = service
        self.authenticate = authenticate

    @staticmethod
    def _segments(path: str) -> list[str]:
        parts = [part for part in urlsplit(path).path.split("/") if part]
        if len(parts) < 2 or parts[0:2] != ["platform", "v1"]:
            raise ValueError("management path must use /platform/v1")
        return parts[2:]

    def dispatch(self, method: str, path: str, headers: Any, body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
        principal = self.authenticate(headers)
        if principal is None:
            return 401, {"error": "invalid_session"}
        actor = str(principal.get("user_id") or principal.get("email") or "unknown")
        method = method.upper()
        parts = self._segments(path)
        body = body or {}
        if not parts:
            return 200, {"service": "research-os-api-management", "namespace": "/platform/v1", "status": "ready"}

        # Nested collections.
        if parts[0] == "developer-portal":
            project_id = parts[1] if len(parts) > 1 else str(body.get("project_id", "")).strip()
            if method == "GET":
                return 200, self.service.get("portals", project_id)
            if method in {"POST", "PATCH"}:
                if method == "POST":
                    payload = dict(body); payload["project_id"] = project_id
                    return 201, self.service.create("portals", payload, actor=actor)
                return 200, self.service.update("portals", project_id, body, actor=actor)

        if parts[0] == "applications" and len(parts) >= 3 and parts[2] == "keys":
            application_id = parts[1]
            if method == "GET":
                values = [value for value in self.service.list("api_keys") if value.get("application_id") == application_id]
                return 200, {"items": values, "count": len(values)}
            if method == "POST":
                payload = dict(body); payload["application_id"] = application_id
                return 201, self.service.create_api_key(payload, actor=actor)

        if parts[0] in {"apis", "versions", "plans", "applications", "products", "routes", "webhooks"} and len(parts) >= 3:
            parent, identifier, action = parts[0], parts[1], parts[2]
            if action in {"publish", "disable", "enable", "release", "retire", "revoke", "rotate"}:
                if action in {"revoke", "rotate"} and parent == "applications":
                    if action == "revoke":
                        return 200, self.service.revoke_api_key(identifier, actor=actor)
                    return 200, self.service.rotate_api_key(identifier, body, actor=actor)
                return 200, self.service.lifecycle(RESOURCE_BY_SEGMENT[parent], identifier, action, actor=actor)

        # Standard resource collection/item operations.
        resource = RESOURCE_BY_SEGMENT.get(parts[0])
        if resource is None:
            if parts[0] == "usage":
                return 200, {"items": [], "count": 0, "source": "runtime-ledger-projection", "status": "READY"}
            if parts[0] == "costs":
                return 200, {"items": [], "count": 0, "source": "runtime-ledger-projection", "status": "READY"}
            if parts[0] == "audit":
                items = self.service.store.audit()
                return 200, {"items": items, "count": len(items), "source": "management-audit"}
            raise KeyError("unknown management resource")

        if method == "GET" and len(parts) == 1:
            values = self.service.list(resource)
            return 200, {"items": values, "count": len(values)}
        if method == "POST" and len(parts) == 1:
            return 201, self.service.create(resource, body, actor=actor)
        if len(parts) >= 2:
            identifier = parts[1]
            if method == "GET":
                return 200, self.service.get(resource, identifier)
            if method == "PATCH":
                return 200, self.service.update(resource, identifier, body, actor=actor)
        raise KeyError("unsupported management operation")
