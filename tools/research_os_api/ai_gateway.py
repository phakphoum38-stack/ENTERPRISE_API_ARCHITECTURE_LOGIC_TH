#!/usr/bin/env python3
"""Compatibility provider gateway report backed by the canonical readiness owner.

This module intentionally contains no provider-selection or credential logic.
It preserves the V3 transport import used by ``v2_server`` while delegating all
status computation to ``provider_readiness.inspect_all`` so there remains one
source of truth and secret values are never returned.
"""

from __future__ import annotations

from typing import Any

from provider_readiness import inspect_all


def gateway_report() -> dict[str, Any]:
    """Return the canonical, secret-safe provider readiness report."""
    return inspect_all()
