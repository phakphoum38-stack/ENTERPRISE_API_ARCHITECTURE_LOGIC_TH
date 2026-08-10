#!/usr/bin/env python3
"""Integration-only separation contract between independent Research OS owners.

This file belongs to the unified integration layer. It is intentionally excluded
from the standalone file-owner distribution package.
"""

from __future__ import annotations

from typing import Any


OWNER_SEPARATION_CONTRACT = "research-os-owner-separation-v1"


class OwnerSeparationContract:
    def manifest(self) -> dict[str, Any]:
        return {
            "contract": OWNER_SEPARATION_CONTRACT,
            "security_owner": "CyberWebSecurityStandard",
            "file_owner": "FileOwnershipBoundary",
            "shared_authority": False,
            "security_may_change_file_owner": False,
            "security_may_grant_file_acl": False,
            "file_owner_may_override_security_policy": False,
            "file_owner_may_disable_security_controls": False,
            "integration_mode": "explicit_contract_only",
            "standalone_owner_package_contains_security_owner": False,
        }


OWNER_SEPARATION = OwnerSeparationContract()


__all__ = [
    "OWNER_SEPARATION",
    "OWNER_SEPARATION_CONTRACT",
    "OwnerSeparationContract",
]
