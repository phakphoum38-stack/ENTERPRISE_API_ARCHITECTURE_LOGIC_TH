#!/usr/bin/env python3
"""Validate Research OS Identity & Access Convergence Wave 1."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current/RESEARCH_OS_AUTHORIZATION_CONVERGENCE_CONTRACT.json"
MAPPING = ROOT / "current/RESEARCH_OS_IDENTITY_ACCESS_WAVE_1_MAP.json"

REQUIRED = (
    "tools/research_os_api/api_auth.py",
    "tools/research_os_api/auth_session.py",
    "tools/research_os_api/identity_context.py",
    "owner_special/research_os_friend/policy.py",
    "tools/control_center_capability_registry.py",
    "apps/research_os_flutter/lib/src/ui/enterprise_navigation.dart",
    "apps/research_os_flutter/lib/src/api/research_os_api_client.dart",
    "current/RESEARCH_OS_OWNER_EXPERIENCE_PLATFORM_CONTRACT.json",
)

def fail(message: str) -> None:
    print(f"IDENTITY_ACCESS_WAVE_1=FAIL: {message}")
    raise SystemExit(1)

def main() -> None:
    if not CONTRACT.is_file() or not MAPPING.is_file():
        fail("wave 1 contract or map is missing")
    for path in REQUIRED:
        if not (ROOT / path).is_file():
            fail(f"missing authority anchor: {path}")

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))

    if contract.get("contract_id") != "research-os-auth-authorization-convergence-v1":
        fail("unexpected contract id")
    if contract.get("status") != "ACTIVE":
        fail("contract is not ACTIVE")
    if mapping.get("map_id") != "research-os-identity-access-wave-1":
        fail("unexpected wave map id")
    if mapping.get("base_sha") != "79b2a2f22ffdc11e97a29912a48b854bd1add37d":
        fail("wave map is not based on current main")

    owner = contract["owner"]
    if owner["role"] != "OWNER" or not owner["highest_privilege"]:
        fail("Owner privilege invariant drifted")
    if owner["resource_or_scope_bound"] is not False:
        fail("Owner must remain unbounded by resource/scope")
    if owner["authority_is_server_derived"] is not True:
        fail("Owner authority must remain server-derived")

    identity = contract["identity"]
    if identity["source"] != "/v1/auth/status" or identity["server_derived"] is not True:
        fail("identity source is not server-derived /v1/auth/status")
    if identity["client_may_override"] is not False:
        fail("client identity override is forbidden")

    authorization = contract["authorization"]
    if authorization["authority"] != "owner_special/research_os_friend/policy.py:OwnerPolicy":
        fail("authorization authority drifted")
    if any(authorization[key] is not False for key in (
        "client_may_grant", "client_may_override",
        "ui_may_authorize", "ui_may_execute", "ui_may_approve",
    )):
        fail("client/UI authorization authority must remain disabled")

    capability = contract["capability_convergence"]
    if capability["google_sign_in"] != "HOLD":
        fail("google_sign_in must remain HOLD until capability proof exists")
    if capability["must_not_infer_permission"] is not True:
        fail("unbound capability must not infer permission")

    navigation = (ROOT / "apps/research_os_flutter/lib/src/ui/enterprise_navigation.dart").read_text(encoding="utf-8")
    if "destinationId: 'google_sign_in'" not in navigation:
        fail("canonical google_sign_in destination is missing")
    if "destinationId: 'owner'" not in navigation:
        fail("canonical owner destination is missing")
    if "capabilityId: 'auth'" in navigation:
        fail("unproven auth capability was promoted")

    policy = (ROOT / "owner_special/research_os_friend/policy.py").read_text(encoding="utf-8")
    if "class OwnerPolicy" not in policy or "authorize_request" not in policy:
        fail("OwnerPolicy source anchor is missing")

    print("IDENTITY_ACCESS_WAVE_1=PASS")
    print("IDENTITY_AUTHORITY=SERVER_DERIVED")
    print("AUTHORIZATION_AUTHORITY=OWNER_POLICY")
    print("OWNER_AUTHORITY=UNBOUNDED")
    print("GOOGLE_SIGN_IN_CAPABILITY=HOLD")

if __name__ == "__main__":
    main()
