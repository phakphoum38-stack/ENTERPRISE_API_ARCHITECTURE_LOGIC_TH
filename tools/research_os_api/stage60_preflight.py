#!/usr/bin/env python3
"""Stage 60 preflight helper.

Runs only against implementation that is actually present in the checked-out
revision. It deliberately does not fabricate Browser Use Cloud modules,
credentials, or simulator files.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_DIR = ROOT / "tools" / "research_os_api"

REQUIRED = [
    API_DIR / "server.py",
    API_DIR / "test_api.py",
]
OPTIONAL_BROWSER_USE = [
    API_DIR / "browser_use_cloud.py",
    API_DIR / "test_browser_use_cloud.py",
    API_DIR / "browser_use_cloud_simulator.py",
]


def main() -> int:
    print("=== STAGE 60 PREFLIGHT ===")
    print(f"revision root: {ROOT}")

    missing = [str(p.relative_to(ROOT)) for p in REQUIRED if not p.is_file()]
    if missing:
        print("FAIL: required implementation files are missing:")
        for item in missing:
            print(f"  - {item}")
        return 1

    print("Required Research OS API files: OK")

    print("Browser Use implementation inventory:")
    for path in OPTIONAL_BROWSER_USE:
        state = "PRESENT" if path.is_file() else "ABSENT"
        print(f"  [{state}] {path.relative_to(ROOT)}")

    print("Running the tests that actually exist in this revision...")
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-p", "test*.py", "-v"],
        cwd=API_DIR,
        check=False,
    )
    if result.returncode != 0:
        print("FAIL: existing API test suite is not green.")
        return result.returncode

    browser_test = API_DIR / "test_browser_use_cloud.py"
    if browser_test.is_file():
        print("Browser Use test module is present; it must be included in the generated smoke workflow.")
    else:
        print("Browser Use test module is not present; Stage 60 must not invoke it yet.")

    print("STAGE 60 PREFLIGHT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
