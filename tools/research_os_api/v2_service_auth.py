#!/usr/bin/env python3
"""Exposure-aware authentication boundary for the primary Research OS service.

Loopback remains the default local-first transport and does not require a shared
application secret. Any non-loopback bind is fail-closed and must use the
existing short-lived signed identity assertion contract.
"""
from __future__ import annotations

import ipaddress
import os
from collections.abc import Mapping

from developer_identity import (
    IdentityAssertionError,
    IdentityAssertionVerifier,
    VerifiedIdentity,
)


class ServiceExposureAuthError(PermissionError):
    """Raised when a non-loopback service request cannot be authenticated."""


def is_loopback_host(host: str | None) -> bool:
    value = (host or "").strip().lower()
    if value in {"localhost", "ip6-localhost"}:
        return True
    if not value:
        return False
    try:
        return ipaddress.ip_address(value).is_loopback
    except ValueError:
        return False


def service_bind_host(default: str = "127.0.0.1") -> str:
    return (
        os.environ.get("RESEARCH_OS_API_HOST")
        or os.environ.get("HOST")
        or default
    ).strip()


def verify_service_request(
    headers: Mapping[str, str],
    *,
    bind_host: str | None = None,
    secret: str | None = None,
    max_age_seconds: int | None = None,
) -> VerifiedIdentity | None:
    """Allow loopback directly; require a signed identity on exposed binds."""
    host = (bind_host if bind_host is not None else service_bind_host()).strip()
    if is_loopback_host(host):
        return None

    configured_secret = (
        secret
        if secret is not None
        else os.environ.get("RESEARCH_OS_IDENTITY_PROXY_SECRET", "")
    ).strip()
    if not configured_secret:
        raise ServiceExposureAuthError(
            "non-loopback Research OS service requires signed identity configuration"
        )

    if max_age_seconds is None:
        raw_max_age = (
            os.environ.get("RESEARCH_OS_IDENTITY_ASSERTION_MAX_AGE") or "120"
        ).strip()
        try:
            max_age_seconds = int(raw_max_age)
        except ValueError as exc:
            raise ServiceExposureAuthError(
                "identity assertion max age configuration is invalid"
            ) from exc

    try:
        verifier = IdentityAssertionVerifier(
            configured_secret,
            max_age_seconds=max_age_seconds,
        )
        return verifier.verify(headers)
    except IdentityAssertionError as exc:
        raise ServiceExposureAuthError(str(exc)) from exc


__all__ = [
    "ServiceExposureAuthError",
    "is_loopback_host",
    "service_bind_host",
    "verify_service_request",
]
