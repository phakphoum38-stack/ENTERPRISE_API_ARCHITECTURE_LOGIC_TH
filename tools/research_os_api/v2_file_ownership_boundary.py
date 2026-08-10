#!/usr/bin/env python3
"""Explicit file ownership boundary for Research OS.

This owner exists to keep filesystem/document ownership authority separate from
Cyber Web Security. It is a boundary contract, not an operating-system ACL
implementation: it does not change owners, grant permissions, or inspect private
file metadata by itself.
"""

from __future__ import annotations

from typing import Any


FILE_OWNERSHIP_CONTRACT = "research-os-file-ownership-boundary-v1"
FILE_OWNERSHIP_VERSION = "2026.08"


class FileOwnershipBoundary:
    """Declare the canonical ownership boundary without performing mutations."""

    def manifest(self) -> dict[str, Any]:
        return {
            "contract": FILE_OWNERSHIP_CONTRACT,
            "version": FILE_OWNERSHIP_VERSION,
            "owner": "FileOwnershipBoundary",
            "scope": [
                "file_ownership_policy_boundary",
                "filesystem_acl_boundary",
                "document_ownership_boundary",
                "storage_authorization_handoff",
            ],
            "implementation_state": "boundary_only",
            "operating_system_acl_backend": False,
            "changes_file_owner": False,
            "grants_file_acl": False,
            "reads_private_file_metadata": False,
            "cyber_security_authority": False,
            "web_security_policy_authority": False,
            "authorization_source": "dedicated_file_ownership_backend_required",
            "cross_owner_contract": self.cyber_boundary(),
        }

    @staticmethod
    def cyber_boundary() -> dict[str, Any]:
        return {
            "separate_from_cyber_web_security": True,
            "cyber_web_owner": "CyberWebSecurityStandard",
            "file_ownership_owner": "FileOwnershipBoundary",
            "cyber_may_change_file_owner": False,
            "cyber_may_grant_file_acl": False,
            "file_owner_may_override_cyber_policy": False,
            "file_owner_may_disable_security_controls": False,
            "shared_authority": False,
            "integration_mode": "explicit_contract_only",
        }

    def plan(self) -> dict[str, Any]:
        """Return a read-only ownership plan until a dedicated backend is added."""
        return {
            "contract": FILE_OWNERSHIP_CONTRACT,
            "owner": "FileOwnershipBoundary",
            "mode": "boundary_only",
            "ownership_change_performed": False,
            "acl_change_performed": False,
            "requires_dedicated_backend_for_mutation": True,
            "requires_explicit_authorization_for_mutation": True,
            "cyber_security_involved": False,
        }


FILE_OWNERSHIP = FileOwnershipBoundary()


__all__ = [
    "FILE_OWNERSHIP",
    "FILE_OWNERSHIP_CONTRACT",
    "FILE_OWNERSHIP_VERSION",
    "FileOwnershipBoundary",
]
