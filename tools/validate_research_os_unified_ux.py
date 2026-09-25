#!/usr/bin/env python3
"""Validate the Platform-owned Research OS unified UX contract."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current/RESEARCH_OS_UNIFIED_UX_LIGHT_BEAM_CONTRACT.json"
REQUIRED_COLORS = {
    "background", "surface", "surface_low", "surface_high", "text_primary",
    "text_secondary", "outline", "primary", "secondary", "blue",
    "success", "warning", "error", "info",
}
REQUIRED_STATES = {
    "IDLE", "FOCUS", "ACTIVE", "PROCESSING", "SUCCESS", "WARNING", "ERROR",
}


def validate() -> list[str]:
    errors: list[str] = []
    if not CONTRACT.is_file():
        return [f"missing contract: {CONTRACT.relative_to(ROOT)}"]

    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if data.get("status") != "ACTIVE":
        errors.append("contract must be ACTIVE")
    if data.get("authority") != "PLATFORM":
        errors.append("UX authority must remain PLATFORM")
    if data.get("visual_language", {}).get("effect") != "UPWARD_LIGHT_BEAM":
        errors.append("light-beam effect must be UPWARD_LIGHT_BEAM")
    if set(data.get("surfaces", [])) != {"WINDOWS", "WEB", "IOS"}:
        errors.append("surface set must be Windows/Web/iOS")

    colors = data.get("colors", {})
    missing = REQUIRED_COLORS - set(colors)
    if missing:
        errors.append(f"missing colors: {sorted(missing)}")

    for name in REQUIRED_COLORS:
        value = colors.get(name)
        if not isinstance(value, str) or len(value) != 7 or not value.startswith("#"):
            errors.append(f"invalid color token: {name}")

    states = data.get("states", {})
    missing_states = REQUIRED_STATES - set(states)
    if missing_states:
        errors.append(f"missing UX states: {sorted(missing_states)}")

    beam = data.get("light_beam", {})
    if beam.get("direction") != "UPWARD":
        errors.append("light beam direction must be UPWARD")
    if beam.get("persistent_background_beam") is not False:
        errors.append("persistent background beam must be disabled")
    if not data.get("rules") or not data.get("legacy_policy"):
        errors.append("UX governance rules and legacy policy are required")

    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        print("UNIFIED_UX=FAIL")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)
    print("UNIFIED_UX=PASS")
