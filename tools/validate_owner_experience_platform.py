#!/usr/bin/env python3
"""Validate the Owner Experience Platform convergence contract."""
from __future__ import annotations
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current" / "RESEARCH_OS_OWNER_EXPERIENCE_PLATFORM_CONTRACT.json"
def fail(message: str) -> None:
    raise SystemExit(f"OWNER_EXPERIENCE_PLATFORM=FAIL: {message}")
def main() -> None:
    if not CONTRACT.is_file(): fail("canonical platform contract is missing")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    required = (
        contract["canonical"]["product_ui_root"], contract["canonical"]["navigation_registry"],
        contract["canonical"]["owner_surface"], contract["canonical"]["ios_source"],
        contract["canonical"]["windows_source"], contract["canonical"]["web_source"],
        contract["owner_special"]["runtime_root"], contract["owner_special"]["runtime_boundary"],
        contract["proof"]["owner_flutter_test"], contract["proof"]["surface_parity_test"],
        contract["proof"]["ios_workflow"], contract["proof"]["ios_reconciliation_workflow"],
    )
    missing = [path for path in required if not (ROOT / path).exists()]
    if missing: fail("missing canonical anchors: " + ", ".join(missing))
    owner = contract["owner"]
    if owner["highest_privilege"] is not True or owner["resource_or_scope_bound"] is not False:
        fail("Owner authority boundary drifted")
    if any(owner[key] is not False for key in ("client_may_grant_authority","ui_may_authorize","ui_may_execute","ui_may_approve","ui_may_release")):
        fail("Owner UI authority boundary drifted")
    owner_special = contract["owner_special"]
    if owner_special["canonical_product_ui"] is not False: fail("Owner Special runtime was promoted to canonical product UI")
    if owner_special["separate_navigation_authority"] is not False: fail("Owner Special acquired duplicate navigation authority")
    navigation = (ROOT / contract["navigation"]["single_source_of_truth"]).read_text(encoding="utf-8")
    if "const researchNavigationItems" not in navigation or navigation.count("const researchNavigationItems") != 1:
        fail("canonical navigation registry is missing or duplicated")
    legacy_v5 = ROOT / "apps/research_os_flutter/lib/src/ui_v5/v5_workspace_route.dart"
    if legacy_v5.is_file() and "static const all =" in legacy_v5.read_text(encoding="utf-8"):
        fail("V5 navigation contains a second hard-coded navigation registry")
    legacy_ios_workflow = ROOT / contract["proof"]["ios_reconciliation_workflow"]
    ios_text = legacy_ios_workflow.read_text(encoding="utf-8")
    forbidden = ("flutter build ios","Runner.xcodeproj/project.pbxproj","ios/Runner/Info.plist","working-directory: owner_special/flutter_app")
    if any(token in ios_text for token in forbidden): fail("legacy Owner Special iOS workflow still contains a build/source authority")
    canonical_ios = (ROOT / contract["proof"]["ios_workflow"]).read_text(encoding="utf-8")
    if "apps/research_os_flutter" not in canonical_ios: fail("canonical iOS workflow is not bound to shared Research OS surface")
    if (ROOT / "owner_special/flutter_app/ios").exists(): fail("Owner Special iOS source unexpectedly exists")
    if contract["authority"]["final_gate_is_single_release_authority"] is not True: fail("Final Gate release authority drifted")
    print("OWNER_EXPERIENCE_PLATFORM=PASS")
    print("CANONICAL_UI=apps/research_os_flutter")
    print("CANONICAL_NAVIGATION=enterprise_navigation.dart")
    print("OWNER_SPECIAL=RUNTIME_BOUNDARY_ONLY")
    print("IOS=SHARED_CANONICAL_SURFACE")
    print("RELEASE_AUTHORITY=FINAL_GATE")
if __name__ == "__main__": main()
