"""Canonical filesystem-safe storage keys for Research OS identities.

The canonical identity (for example ``google:123``) must never be rewritten
just to satisfy filesystem rules. This module provides one deterministic,
platform-neutral storage key for every user-scoped persistent store.
"""
from __future__ import annotations

import hashlib


def storage_key(user_id: str) -> str:
    """Return a deterministic filesystem-safe key for a canonical user id."""
    value = str(user_id or "").strip()
    if not value:
        raise ValueError("user_id is required")
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return "u_" + digest
