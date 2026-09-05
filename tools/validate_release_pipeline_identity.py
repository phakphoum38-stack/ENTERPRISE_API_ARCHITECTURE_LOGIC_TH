from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
OWNER_WORKFLOW = WORKFLOWS / "owner-special-friend.yml"
RESEARCH_WORKFLOW = WORKFLOWS / "research-os-windows-artifact.yml"
OWNER_MANIFEST = ROOT / "owner_special" / "OWNER_MANIFEST.json"
OWNER_IDENTITY_GATE = ROOT / "owner_special" / "scripts" / "verify-owner-build-identity.ps1"
OWNER_EXE = "research_os_owner_special.exe"
OWNER_SETUP = "Research-OS-Owner-Special-Setup-1.3.1-x64.exe"


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []

    if not WORKFLOWS.is_dir():
        fail(errors, f"Missing workflow directory: {WORKFLOWS}")
    else:
        workflow_files = sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml"))
        if not workflow_files:
            fail(errors, "No GitHub Actions workflow files found.")
        for path in workflow_files:
            text = path.read_text(encoding="utf-8")
            if "flutter create" in text.lower():
                fail(
                    errors,
                    f"FORBIDDEN_RELEASE_SCAFFOLD: {path.relative_to(ROOT)} contains 'flutter create'. "
                    "Canonical release workflows must consume committed platform sources.",
                )

            rel = path.relative_to(ROOT).as_posix()
            if rel != OWNER_WORKFLOW.relative_to(ROOT).as_posix():
                if OWNER_EXE in text or OWNER_SETUP in text or "owner_special/flutter_app" in text:
                    fail(
                        errors,
                        f"OWNER_LEAKAGE: non-Owner workflow {rel} references Owner-specific identity/source.",
                    )

        if OWNER_WORKFLOW.is_file():
            owner_text = OWNER_WORKFLOW.read_text(encoding="utf-8")
            required = [
                "owner_special/flutter_app",
                "verify-owner-build-identity.ps1",
                OWNER_EXE,
                "stage-owner-installer.ps1",
                "build_bundle.py",
            ]
            for token in required:
                if token not in owner_text:
                    fail(errors, f"OWNER_GATE_INCOMPLETE: {OWNER_WORKFLOW.name} is missing required token: {token}")
        else:
            fail(errors, f"Missing dedicated Owner workflow: {OWNER_WORKFLOW}")

        if RESEARCH_WORKFLOW.is_file():
            research_text = RESEARCH_WORKFLOW.read_text(encoding="utf-8")
            forbidden = [OWNER_EXE, OWNER_SETUP, "owner_special/flutter_app"]
            for token in forbidden:
                if token in research_text:
                    fail(errors, f"RESEARCH_OS_OWNER_LEAK: {RESEARCH_WORKFLOW.name} contains {token}")

    if not OWNER_MANIFEST.is_file():
        fail(errors, f"Missing Owner manifest: {OWNER_MANIFEST}")
    else:
        try:
            manifest = json.loads(OWNER_MANIFEST.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(errors, f"Owner manifest is invalid JSON: {exc}")
        else:
            if manifest.get("edition") != "owner-special":
                fail(errors, "Owner manifest edition must be 'owner-special'.")
            if manifest.get("owner_only") is not True:
                fail(errors, "Owner manifest owner_only must be true.")

    if not OWNER_IDENTITY_GATE.is_file():
        fail(errors, f"Missing Owner identity verifier: {OWNER_IDENTITY_GATE}")

    if errors:
        print("RELEASE_PIPELINE_IDENTITY_GATE=FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("RELEASE_PIPELINE_IDENTITY_GATE=PASS")
    print("- All GitHub Actions workflows are free of flutter create release scaffolding.")
    print("- Owner identity/source is isolated to the dedicated Owner workflow.")
    print("- Dedicated Owner workflow contains identity, installer, and bundle gates.")
    print("- Research OS Windows artifact workflow contains no Owner identity/source.")
    print("- Owner manifest and identity verifier are present and valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
