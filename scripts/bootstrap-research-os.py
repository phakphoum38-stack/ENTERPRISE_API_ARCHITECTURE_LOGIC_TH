#!/usr/bin/env python3
"""Bootstrap a verified Research OS package from local or cloud-synchronized storage."""
from __future__ import annotations

import argparse
from pathlib import Path

from tools.research_os_api.runner_installer import (
    InstallationError,
    build_bootstrap_plan,
    install_verified_package,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True, type=Path, help="Package directory, including PACKAGE_MANIFEST.json")
    parser.add_argument("--target", required=True, type=Path, help="Local installation directory")
    parser.add_argument("--platform", required=True, help="Host platform profile")
    parser.add_argument("--architecture", required=True, help="Host architecture profile")
    args = parser.parse_args()

    try:
        plan = build_bootstrap_plan(
            source=args.package,
            platform_name=args.platform,
            architecture=args.architecture,
        )
        manifest = args.package / "PACKAGE_MANIFEST.json"
        installed = install_verified_package(args.package, manifest, args.target)
    except InstallationError as exc:
        print(f"RUNNER_BOOTSTRAP=REJECT: {exc}")
        return 1

    print("RUNNER_BOOTSTRAP=PASS")
    print(f"PACKAGE_ID={installed.package_id}")
    print(f"VERSION={installed.version}")
    print(f"SOURCE_SHA={installed.source_sha}")
    print(f"TARGET={args.target}")
    print("PLAN=" + "->".join(plan))
    print("CLOUD_DRIVE_IS_DISTRIBUTION_ONLY=TRUE")
    print("AUTHORIZATION_GRANTED=FALSE")
    print("RELEASE_AUTHORITY=FINAL_GATE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
