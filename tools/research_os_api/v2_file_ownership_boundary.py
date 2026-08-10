#!/usr/bin/env python3
"""Standalone file ownership boundary for Research OS.

This module defines filesystem and document ownership responsibility only. It is
a boundary contract, not an operating-system ACL implementation, and performs no
owner or permission mutation by itself.
"""

from __future__ import annotations

from typing import Any


FILE_OWNERSHIP_CONTRACT = "research-os-file-ownership-boundary-v2"
FILE_OWNERSHIP_VERSION = "2026.08"


class FileOwnershipBoundary:
    """Declare file-ownership responsibility without performing mutations."""

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
            "authorization_source": "dedicated_file_ownership_backend_required",
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
        }


FILE_OWNERSHIP = FileOwnershipBoundary()


__all__ = [
    "FILE_OWNERSHIP",
    "FILE_OWNERSHIP_CONTRACT",
    "FILE_OWNERSHIP_VERSION",
    "FileOwnershipBoundary",
]
