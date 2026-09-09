"""Pre-test execution integrity fence for AEOS/Research OS CI.

The gate is intentionally read-only. It proves that CI is executing the expected
revision and that the authority API has completed its contract migration before
the broader test suite is allowed to run.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "owner_special" / "research_os_friend" / "aeos_authority_risk.py"
AUTHORITY_TEST = ROOT / "owner_special" / "tests" / "test_aeos_assurance_fabric_expansion.py"
CONTRACT = ROOT / "current" / "AEOS_ASSURANCE_FABRIC_CONTRACT.json"
UNIVERSE = ROOT / "current" / "AEOS_GLOBAL_ASSURANCE_UNIVERSE.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def authority_signature() -> list[str]:
    tree = ast.parse(AUTHORITY.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "evaluate_authority_risk":
            return [arg.arg for arg in node.args.args + node.args.kwonlyargs]
    raise RuntimeError("evaluate_authority_risk not found")


def assert_contract_migration() -> None:
    args = authority_signature()
    forbidden = {"authority_verified", "capability_verified", "provenance_verified"}
    if forbidden.intersection(args):
        raise RuntimeError("deprecated raw authority verification arguments remain in API")
    required = {"human_approval", "verification_proof"}
    if not required.issubset(args):
        raise RuntimeError("AuthorityVerificationProof contract is not enforced by API signature")
    test_text = AUTHORITY_TEST.read_text(encoding="utf-8")
    if "TypeError" not in test_text or "authority_verified=True" not in test_text:
        raise RuntimeError("negative contract migration regression is missing")


def assert_import_origin() -> None:
    sys.path.insert(0, str(AUTHORITY.parent))
    import aeos_authority_risk  # type: ignore
    origin = Path(inspect.getfile(aeos_authority_risk)).resolve()
    if origin != AUTHORITY.resolve():
        raise RuntimeError(f"authority module imported from unexpected origin: {origin}")


def main() -> int:
    expected = os.environ.get("AEOS_EXPECTED_SHA", "").strip().lower()
    actual = git_sha().lower()
    if not expected or len(expected) != 40 or any(c not in "0123456789abcdef" for c in expected):
        raise RuntimeError("AEOS_EXPECTED_SHA must be an exact 40-character lowercase SHA")
    if actual != expected:
        raise RuntimeError(f"CHECKOUT_SHA_MISMATCH expected={expected} actual={actual}")
    for path in (AUTHORITY, AUTHORITY_TEST, CONTRACT, UNIVERSE):
        if not path.is_file():
            raise RuntimeError(f"required provenance input missing: {path.relative_to(ROOT)}")
    assert_import_origin()
    assert_contract_migration()
    manifest = {
        "expected_sha": expected,
        "actual_sha": actual,
        "python": sys.version.split()[0],
        "authority_sha256": sha256(AUTHORITY),
        "authority_test_sha256": sha256(AUTHORITY_TEST),
        "contract_sha256": sha256(CONTRACT),
        "universe_sha256": sha256(UNIVERSE),
        "authority_signature": authority_signature(),
        "status": "PASS",
    }
    print(json.dumps(manifest, sort_keys=True))
    print("AEOS_EXECUTION_INTEGRITY=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"AEOS_EXECUTION_INTEGRITY=FAIL: {exc}")
        raise
