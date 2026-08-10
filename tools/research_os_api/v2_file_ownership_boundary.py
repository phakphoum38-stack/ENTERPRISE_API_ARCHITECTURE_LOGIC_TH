#!/usr/bin/env python3
"""Research OS File Ownership boundary.

This module defines exactly three responsibilities: file ownership, filesystem
ACL, and document ownership. It does not implement any other subsystem.
"""

from __future__ import annotations

from typing import Any


FILE_OWNERSHIP_CONTRACT = "research-os-file-ownership-boundary-v2"
FILE_OWNERSHIP_VERSION = "2026.08"


class FileOwnershipBoundary:
    """Declare the three File Ownership responsibilities."""

    def manifest(self) -> dict[str, Any]:
        return {
            "contract": FILE_OWNERSHIP_CONTRACT,
            "version": FILE_OWNERSHIP_VERSION,
            "owner": "FileOwnershipBoundary",
            "scope": [
                "file_ownership",
                "filesystem_acl",
                "document_ownership",
            ],
            "implementation_state": "boundary_only",
            "changes_file_owner": False,
            "grants_file_acl": False,
            "changes_document_owner": False,
        }

    def plan(self) -> dict[str, Any]:
        """Return a read-only plan for the three ownership responsibilities."""
        return {
            "contract": FILE_OWNERSHIP_CONTRACT,
            "owner": "FileOwnershipBoundary",
            "scope": [
                "file_ownership",
                "filesystem_acl",
                "document_ownership",
            ],
            "mode": "boundary_only",
            "ownership_change_performed": False,
            "acl_change_performed": False,
            "document_ownership_change_performed": False,
        }


FILE_OWNERSHIP = FileOwnershipBoundary()


__all__ = [
    "FILE_OWNERSHIP",
    "FILE_OWNERSHIP_CONTRACT",
    "FILE_OWNERSHIP_VERSION",
    "FileOwnershipBoundary",
]
