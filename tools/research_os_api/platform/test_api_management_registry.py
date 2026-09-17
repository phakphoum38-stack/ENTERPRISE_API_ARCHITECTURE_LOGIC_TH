"""Regression tests for the API Management Platform registry boundary."""
from datetime import datetime, timezone

import pytest

from api_management_models import API, APIEndpoint, APIVersion, APIKey, Organization, Plan, Project, Scope, Application, GatewayRoute
from api_management_registry import ManagementRegistry


def registry() -> ManagementRegistry:
    r = ManagementRegistry()
    r.add_organization(Organization("org-1", "Research OS"))
    r.add_project(Project("proj-1", "org-1", "Developer Platform"))
    r.add_application(Application("app-1", "proj-1", "Demo App"))
    r.add_scope(Scope("scope.read", "read"))
    r.add_scope(Scope("scope.write", "write"))
    r.add_api(API("api-1", "proj-1", "Example API"))
    r.add_version(APIVersion("ver-1", "api-1", "v1"))
    return r


def test_registry_accepts_canonical_hierarchy() -> None:
    r = registry()
    endpoint = r.add_endpoint(APIEndpoint("ep-1", "ver-1", "GET", "/items", "listItems", ("scope.read",)))
    route = r.add_route(GatewayRoute("route-1", endpoint.endpoint_id, "local://items"))
    assert endpoint.endpoint_id == "ep-1"
    assert route.endpoint_id == endpoint.endpoint_id


def test_unknown_scope_fails_closed() -> None:
    r = registry()
    with pytest.raises(ValueError, match="unknown scope"):
        r.add_endpoint(APIEndpoint("ep-1", "ver-1", "GET", "/items", "listItems", ("scope.missing",)))


def test_cross_project_product_reference_fails_closed() -> None:
    r = registry()
    r.add_organization(Organization("org-2", "Other"))
    r.add_project(Project("proj-2", "org-2", "Other Project"))
    r.add_api(API("api-2", "proj-2", "Other API"))
    from api_management_models import APIProduct
    with pytest.raises(ValueError, match="outside its project"):
        r.add_product(APIProduct("product-1", "proj-1", "Mixed", ("api-2",), ()))


def test_api_key_cannot_escape_entitlement_scopes() -> None:
    r = registry()
    key = APIKey("key-1", "app-1", "fp", ("scope.write",), datetime.now(timezone.utc))
    with pytest.raises(ValueError, match="outside its entitlement"):
        r.add_api_key(key, entitlement_scope_ids=("scope.read",))


def test_snapshot_contains_management_metadata_only() -> None:
    r = registry()
    r.add_plan(Plan("plan-1", "proj-1", "Free"))
    snapshot = r.snapshot()
    assert "projects" in snapshot
    assert "plans" in snapshot
    assert "raw_key" not in str(snapshot).lower()
