"""Canonical domain contracts for the Research OS API Management Platform.

This module defines management-plane objects only. Runtime authorization, quota,
budget, admission, routing, usage, and evidence remain owned by the existing
control-plane kernel.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Mapping, Optional, Tuple


class Lifecycle(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass(frozen=True)
class Organization:
    organization_id: str
    name: str


@dataclass(frozen=True)
class Project:
    project_id: str
    organization_id: str
    name: str


@dataclass(frozen=True)
class Application:
    application_id: str
    project_id: str
    name: str
    service_account: bool = False


@dataclass(frozen=True)
class API:
    api_id: str
    project_id: str
    name: str
    lifecycle: Lifecycle = Lifecycle.ACTIVE


@dataclass(frozen=True)
class APIVersion:
    version_id: str
    api_id: str
    version: str
    released: bool = False


@dataclass(frozen=True)
class APIEndpoint:
    endpoint_id: str
    version_id: str
    method: str
    path: str
    operation_id: str
    scopes: Tuple[str, ...] = ()


@dataclass(frozen=True)
class Scope:
    scope_id: str
    name: str
    description: str = ""


@dataclass(frozen=True)
class APIKey:
    key_id: str
    application_id: str
    fingerprint: str
    scopes: Tuple[str, ...]
    created_at: datetime
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None


@dataclass(frozen=True)
class Entitlement:
    entitlement_id: str
    plan_id: str
    scope_ids: Tuple[str, ...] = ()
    quota_policy_id: Optional[str] = None
    rate_limit_policy_id: Optional[str] = None
    budget_id: Optional[str] = None
    policy_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class Plan:
    plan_id: str
    project_id: str
    name: str
    entitlement_ids: Tuple[str, ...] = ()
    lifecycle: Lifecycle = Lifecycle.ACTIVE


@dataclass(frozen=True)
class GatewayRoute:
    route_id: str
    endpoint_id: str
    target: str
    enabled: bool = True


@dataclass(frozen=True)
class Webhook:
    webhook_id: str
    project_id: str
    url: str
    event_types: Tuple[str, ...]
    enabled: bool = True


@dataclass(frozen=True)
class APIProduct:
    product_id: str
    project_id: str
    name: str
    api_ids: Tuple[str, ...] = ()
    plan_ids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class DeveloperPortalMetadata:
    project_id: str
    title: str
    description: str = ""
    explorer_enabled: bool = True
    sdk_languages: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ManagementInvariantViolation(ValueError):
    code: str
    detail: str


def validate_management_model(
    *,
    organization: Organization,
    project: Project,
    application: Application,
    api: API,
    version: APIVersion,
    endpoint: APIEndpoint,
    scopes: Optional[Mapping[str, Scope]] = None,
    plans: Optional[Mapping[str, Plan]] = None,
) -> None:
    """Fail closed when canonical management relationships are inconsistent."""
    scopes = {} if scopes is None else scopes
    plans = {} if plans is None else plans

    if project.organization_id != organization.organization_id:
        raise ManagementInvariantViolation("PROJECT_ORGANIZATION_MISMATCH", "project must belong to organization")
    if application.project_id != project.project_id:
        raise ManagementInvariantViolation("APPLICATION_PROJECT_MISMATCH", "application must belong to project")
    if api.project_id != project.project_id:
        raise ManagementInvariantViolation("API_PROJECT_MISMATCH", "api must belong to project")
    if version.api_id != api.api_id:
        raise ManagementInvariantViolation("VERSION_API_MISMATCH", "version must belong to api")
    if endpoint.version_id != version.version_id:
        raise ManagementInvariantViolation("ENDPOINT_VERSION_MISMATCH", "endpoint must belong to version")
    if endpoint.method.upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
        raise ManagementInvariantViolation("INVALID_HTTP_METHOD", "unsupported HTTP method")
    if not endpoint.path.startswith("/"):
        raise ManagementInvariantViolation("INVALID_ENDPOINT_PATH", "endpoint path must start with /")
    for scope_id in endpoint.scopes:
        if scope_id not in scopes:
            raise ManagementInvariantViolation("UNKNOWN_SCOPE", f"endpoint references unknown scope: {scope_id}")
    for plan in plans.values():
        if plan.project_id != project.project_id:
            raise ManagementInvariantViolation("PLAN_PROJECT_MISMATCH", "plan must belong to project")


def validate_api_key_scope_subset(api_key: APIKey, entitlement_scope_ids: Tuple[str, ...]) -> None:
    """Management records cannot grant a scope outside the entitlement boundary."""
    allowed = set(entitlement_scope_ids)
    unexpected = sorted(set(api_key.scopes) - allowed)
    if unexpected:
        raise ManagementInvariantViolation(
            "API_KEY_SCOPE_ESCALATION",
            "api key contains scopes outside its entitlement: " + ", ".join(unexpected),
        )
