"""Stage 60 bounded helper orchestrator.

20^20 is treated as logical scheduling capacity. It never means spawning
20^20 OS processes. A bounded worker pool executes concrete checks with
queueing, timeout, and fail-fast semantics.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

LOGICAL_CAPACITY = 20**20
DEFAULT_WORKERS = 8
DEFAULT_TIMEOUT_SECONDS = 180


@dataclass(frozen=True)
class Check:
    name: str
    command: tuple[str, ...]
    cwd: Path


def run_check(check: Check, timeout: int) -> tuple[str, int, str]:
    try:
        result = subprocess.run(
            check.command,
            cwd=check.cwd,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        output = (result.stdout + "\n" + result.stderr).strip()
        return check.name, result.returncode, output
    except subprocess.TimeoutExpired:
        return check.name, 124, f"timeout after {timeout}s"
    except OSError as exc:
        return check.name, 127, str(exc)


def build_checks(root: Path) -> list[Check]:
    checks: list[Check] = []
    api_dir = root / "tools" / "research_os_api"
    flutter_dir = root / "apps" / "research_os_flutter"

    if (api_dir / "test_api.py").exists():
        checks.append(
            Check(
                "research-os-api-tests",
                (sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "test*.py", "-v"),
                api_dir,
            )
        )

    chat_e2e = flutter_dir / "tool" / "chat_service_e2e.dart"
    if chat_e2e.exists():
        checks.append(
            Check(
                "chat-service-e2e",
                ("dart", str(chat_e2e.relative_to(root))),
                root,
            )
        )

    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    workers = max(1, min(args.workers, 32))
    root = args.root.resolve()
    checks = build_checks(root)

    print(f"STAGE60 logical_capacity={LOGICAL_CAPACITY}")
    print(f"STAGE60 bounded_workers={workers}")
    print(f"STAGE60 queued_checks={len(checks)}")

    if not checks:
        print("STAGE60 FAIL: no concrete checks were discovered")
        return 2

    failures = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run_check, check, args.timeout) for check in checks]
        for future in concurrent.futures.as_completed(futures):
            name, code, output = future.result()
            status = "PASS" if code == 0 else "FAIL"
            print(f"[{status}] {name} exit={code}")
            if output:
                print(output[-6000:])
            failures += code != 0

    if failures:
        print(f"STAGE60 FAIL: {failures} check(s) failed")
        return 1

    print("STAGE60 PASS: all discovered concrete checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
