#!/usr/bin/env python3
"""Audit primary Research OS surfaces for known pre-unified UX palette remnants."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SURFACES = [
    ROOT / "apps/research_os_flutter/lib/src/research_os_app.dart",
    ROOT / "apps/research_os_flutter/lib/src/ui/research_os_design_tokens.dart",
    ROOT / "apps/research_os_web/app.css",
    ROOT / "owner_special/flutter_app/lib/src/friend_theme.dart",
]
FORBIDDEN_TOKENS = (
    "#9be15d", "#6fbf45", "#c7f98a", "#75c94a", "#d2efb8",
    "#1976d2", "#0c1015", "#101419", "#151a21",
)


def audit() -> list[str]:
    findings: list[str] = []
    for path in SURFACES:
        if not path.is_file():
            findings.append(f"missing production UX surface: {path.relative_to(ROOT)}")
            continue
        text = path.read_text(encoding="utf-8").lower()
        for token in FORBIDDEN_TOKENS:
            if token in text:
                findings.append(f"legacy palette token {token} remains in {path.relative_to(ROOT)}")
    return findings


if __name__ == "__main__":
    findings = audit()
    if findings:
        print("UX_LEGACY_AUDIT=FAIL")
        for finding in findings:
            print(f"- {finding}")
        raise SystemExit(1)
    print("UX_LEGACY_AUDIT=PASS")
