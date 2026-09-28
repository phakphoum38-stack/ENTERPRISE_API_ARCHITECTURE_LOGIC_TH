"""Independent identity and organization boundary for API Management Platform.

This module contains management metadata only. It deliberately has no dependency
on the Runtime API execution or ResourceControlPlane.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class PrincipalType(str, Enum):
    USER = "user"
    SERVICE = "service"
    APPLICATION = "application"


@dataclass(frozen=True)
class ManagementPrincipal:
    principal_id: str
    organization_id: str
    principal_type: PrincipalType
    display_name: str
    active: bool = True


class ManagementIdentityRegistry:
    """Fail-closed metadata registry for management principals and organizations."""

    def __init__(self) -> None:
        self.organizations: Dict[str, object] = {}
        self.principals: Dict[str, ManagementPrincipal] = {}

    def register_organization(self, organization_id: str) -> str:
        self._require_id(organization_id, "organization")
        if organization_id in self.organizations:
            raise ValueError(f"duplicate organization id: {organization_id}")
        self.organizations[organization_id] = organization_id
        return organization_id

    def register_principal(self, principal: ManagementPrincipal) -> ManagementPrincipal:
        self._require_id(principal.principal_id, "principal")
        if principal.organization_id not in self.organizations:
            raise ValueError("principal references unknown organization")
        if principal.principal_id in self.principals:
            raise ValueError(f"duplicate principal id: {principal.principal_id}")
        self.principals[principal.principal_id] = principal
        return principal

    def get_principal(self, principal_id: str) -> ManagementPrincipal:
        try:
            return self.principals[principal_id]
        except KeyError:
            raise KeyError(f"management principal not found: {principal_id}") from None

    @staticmethod
    def _require_id(value: str, kind: str) -> None:
        if not value.strip():
            raise ValueError(f"{kind} id is required")
