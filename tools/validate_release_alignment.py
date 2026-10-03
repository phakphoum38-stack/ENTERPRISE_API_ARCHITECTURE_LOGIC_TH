from __future__ import annotations

import re
from pathlib import Path


class ReleaseAlignmentError(ValueError):
    pass


def validate(root: Path) -> str:
    installer = (root / "installer/research-os.iss").read_text(encoding="utf-8")
    flutter = (root / "apps/research_os_flutter/pubspec.yaml").read_text(encoding="utf-8")
    openapi = (root / "tools/research_os_api/openapi.yaml").read_text(encoding="utf-8")

    installer_match = re.search(r'#define MyAppVersion "([^"]+)"', installer)
    flutter_match = re.search(r"^version:\s*([^+\s]+)", flutter, re.MULTILINE)
    api_match = re.search(
        r"^info:\s*\n(?:.*\n)*?\s+version:\s*([^\s]+)",
        openapi,
        re.MULTILINE,
    )
    if not installer_match or not flutter_match or not api_match:
        raise ReleaseAlignmentError("release version metadata is incomplete")

    versions = {
        "installer": installer_match.group(1),
        "flutter": flutter_match.group(1),
        "api": api_match.group(1),
    }
    if len(set(versions.values())) != 1:
        raise ReleaseAlignmentError(f"release versions do not match: {versions}")
    if r"..\v3\*" not in installer:
        raise ReleaseAlignmentError("installer does not package the V3 source")
    return versions["installer"]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    print(f"release_alignment=OK version={validate(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
