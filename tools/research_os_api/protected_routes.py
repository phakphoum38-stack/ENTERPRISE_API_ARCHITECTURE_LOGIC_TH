"""P0-003 protected Research OS route contract.

This module is intentionally separate from the verified P0-001/P0-002
session primitives.  It defines only which HTTP routes require a verified
Research OS session and which bootstrap/liveness routes remain public.
"""
from __future__ import annotations

from typing import Final

PUBLIC_GET_ROUTES: Final[frozenset[str]] = frozenset(
    {
        "/health",
        "/v1/providers",
        "/v1/auth/google/status",
        "/v1/auth/google/callback",
        "/v1/google-workspace/dashboard",
        "/v1/google-workspace/oauth/status",
        "/v1/google-workspace/oauth/callback",
    }
)

PUBLIC_POST_ROUTES: Final[frozenset[str]] = frozenset(
    {
        "/v1/auth/google/start",
        "/v1/auth/google/signout",
        "/v1/google-workspace/oauth/start",
        "/v1/google-workspace/oauth/disconnect",
        "/v1/google-workspace/services",
    }
)

PROTECTED_GET_ROUTES: Final[frozenset[str]] = frozenset(
    {
        "/v1/conversations/cloud",
        "/v1/memory/search",
        "/v1/knowledge/artifacts",
        "/v1/knowledge/graph",
        "/v1/github/dashboard",
    }
)

PROTECTED_POST_ROUTES: Final[frozenset[str]] = frozenset(
    {
        "/v1/conversations/cloud/sync",
        "/v1/conversations/cloud/delete",
        "/v1/ai/generate",
        "/v1/ai/answer-with-memory",
        "/v1/conversations/analyze",
        "/v1/memory/commit",
    }
)


def is_protected(method: str, path: str) -> bool:
    """Return whether a route must establish a Research OS session first."""
    method = method.upper()
    if method == "GET":
        return path in PROTECTED_GET_ROUTES
    if method == "POST":
        return path in PROTECTED_POST_ROUTES
    return False


def is_public_bootstrap(method: str, path: str) -> bool:
    """Return whether a route is intentionally public/bootstrap-only."""
    method = method.upper()
    if method == "GET":
        return path in PUBLIC_GET_ROUTES
    if method == "POST":
        return path in PUBLIC_POST_ROUTES
    return False
