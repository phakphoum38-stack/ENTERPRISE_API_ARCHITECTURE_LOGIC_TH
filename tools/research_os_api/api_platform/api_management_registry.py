"""Canonical registry for API Management Platform configuration.

The registry owns management metadata and relationship validation only. It is
not an execution engine and must not duplicate authentication, quota, policy,
budget, admission, routing, usage, or evidence logic.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Dict, Iterable, TypeVar

try:
    from tools.research_os_api.api_management_models import (
        API, APIEndpoint, APIKey, APIVersion, APIProduct, Application,
        DeveloperPortalMetadata, Entitlement, GatewayRoute, Organization, Plan,
        Project, Scope, Webhook, validate_api_key_scope_subset,
    )
except ModuleNotFoundError:
    from api_management_models import (
        API, APIEndpoint, APIKey, APIVersion, APIProduct, Application,
        DeveloperPortalMetadata, Entitlement, GatewayRoute, Organization, Plan,
        Project, Scope, Webhook, validate_api_key_scope_subset,
    )

T = TypeVar("T")


class ManagementRegistry:
    """In-memory management registry adapter with fail-closed relationships."""

    def __init__(self) -> None:
        self.organizations: Dict[str, Organization] = {}
        self.projects: Dict[str, Project] = {}
        self.applications: Dict[str, Application] = {}
        self.apis: Dict[str, API] = {}
        self.versions: Dict[str, APIVersion] = {}
        self.endpoints: Dict[str, APIEndpoint] = {}
        self.scopes: Dict[str, Scope] = {}
        self.api_keys: Dict[str, APIKey] = {}
        self.entitlements: Dict[str, Entitlement] = {}
        self.plans: Dict[str, Plan] = {}
        self.routes: Dict[str, GatewayRoute] = {}
        self.webhooks: Dict[str, Webhook] = {}
        self.products: Dict[str, APIProduct] = {}
        self.portals: Dict[str, DeveloperPortalMetadata] = {}

    @staticmethod
    def _put(store: dict[str, T], obj: T, identifier: str) -> T:
        if not identifier.strip():
            raise ValueError("management object id is required")
        if identifier in store:
            raise ValueError(f"duplicate management object id: {identifier}")
        store[identifier] = obj
        return obj

    def add_organization(self, obj: Organization) -> Organization:
        return self._put(self.organizations, obj, obj.organization_id)

    def add_project(self, obj: Project) -> Project:
        if obj.organization_id not in self.organizations:
            raise ValueError("project references unknown organization")
        return self._put(self.projects, obj, obj.project_id)

    def add_application(self, obj: Application) -> Application:
        if obj.project_id not in self.projects:
            raise ValueError("application references unknown project")
        return self._put(self.applications, obj, obj.application_id)

    def add_api(self, obj: API) -> API:
        if obj.project_id not in self.projects:
            raise ValueError("api references unknown project")
        return self._put(self.apis, obj, obj.api_id)

    def add_version(self, obj: APIVersion) -> APIVersion:
        if obj.api_id not in self.apis:
            raise ValueError("version references unknown api")
        return self._put(self.versions, obj, obj.version_id)

    def add_scope(self, obj: Scope) -> Scope:
        return self._put(self.scopes, obj, obj.scope_id)

    def add_endpoint(self, obj: APIEndpoint) -> APIEndpoint:
        version = self.versions.get(obj.version_id)
        if version is None:
            raise ValueError("endpoint references unknown version")
        api = self.apis.get(version.api_id)
        if api is None or api.project_id not in self.projects:
            raise ValueError("endpoint references an invalid api hierarchy")
        if obj.method.upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
            raise ValueError("unsupported HTTP method")
        if not obj.path.startswith("/"):
            raise ValueError("endpoint path must start with /")
        missing = sorted(set(obj.scopes) - self.scopes.keys())
        if missing:
            raise ValueError("endpoint references unknown scopes: " + ", ".join(missing))
        return self._put(self.endpoints, obj, obj.endpoint_id)

    def add_plan(self, obj: Plan) -> Plan:
        if obj.project_id not in self.projects:
            raise ValueError("plan references unknown project")
        return self._put(self.plans, obj, obj.plan_id)

    def add_entitlement(self, obj: Entitlement) -> Entitlement:
        if obj.plan_id not in self.plans:
            raise ValueError("entitlement references unknown plan")
        missing = sorted(set(obj.scope_ids) - self.scopes.keys())
        if missing:
            raise ValueError("entitlement references unknown scopes: " + ", ".join(missing))
        return self._put(self.entitlements, obj, obj.entitlement_id)

    def add_api_key(self, obj: APIKey, *, entitlement_scope_ids: Iterable[str]) -> APIKey:
        if obj.application_id not in self.applications:
            raise ValueError("api key references unknown application")
        validate_api_key_scope_subset(obj, tuple(entitlement_scope_ids))
        return self._put(self.api_keys, obj, obj.key_id)

    def add_route(self, obj: GatewayRoute) -> GatewayRoute:
        if obj.endpoint_id not in self.endpoints:
            raise ValueError("gateway route references unknown endpoint")
        return self._put(self.routes, obj, obj.route_id)

    def add_webhook(self, obj: Webhook) -> Webhook:
        if obj.project_id not in self.projects:
            raise ValueError("webhook references unknown project")
        return self._put(self.webhooks, obj, obj.webhook_id)

    def add_product(self, obj: APIProduct) -> APIProduct:
        if obj.project_id not in self.projects:
            raise ValueError("product references unknown project")
        if any(api_id not in self.apis or self.apis[api_id].project_id != obj.project_id for api_id in obj.api_ids):
            raise ValueError("product contains api outside its project")
        if any(plan_id not in self.plans or self.plans[plan_id].project_id != obj.project_id for plan_id in obj.plan_ids):
            raise ValueError("product contains plan outside its project")
        return self._put(self.products, obj, obj.product_id)

    def set_portal(self, obj: DeveloperPortalMetadata) -> DeveloperPortalMetadata:
        if obj.project_id not in self.projects:
            raise ValueError("developer portal references unknown project")
        if obj.project_id in self.portals:
            raise ValueError("developer portal metadata already exists for project")
        self.portals[obj.project_id] = obj
        return obj

    def get(self, resource: str, identifier: str):
        store = getattr(self, resource, None)
        if not isinstance(store, dict):
            raise KeyError(f"unknown management resource: {resource}")
        try:
            return store[identifier]
        except KeyError:
            raise KeyError(f"management object not found: {resource}/{identifier}") from None

    def snapshot(self) -> dict[str, list[dict]]:
        """Return metadata only; no credential secret or runtime decision state."""
        stores = {
            name: store for name, store in vars(self).items()
            if isinstance(store, dict)
        }
        return {name: [asdict(value) for value in store.values()] for name, store in stores.items()}
