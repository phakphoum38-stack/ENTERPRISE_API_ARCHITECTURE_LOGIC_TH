import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSTITUTION = ROOT / "current" / "ENGINEERING_CONSTITUTION.json"
FIXTURE = ROOT / "current" / "ENGINEERING_CONSTITUTION_FIXTURE.json"
SCHEMA_VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)$")
VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"constitution_load_error: {exc}"]

    c = payload.get("constitution") if "constitution" in payload else payload
    if not isinstance(c, dict):
        return ["constitution must be an object"]

    required = ["schema_version", "status", "constitution_id", "version", "principles", "authority_levels", "high_risk_action_classes", "governance_rules", "amendment_lifecycle", "amendment_requirements", "emergency_protocol", "enforcement"]
    for key in required:
        if key not in c:
            errors.append(f"missing required field: {key}")
    if c.get("status") != "CANONICAL":
        errors.append("status must be CANONICAL")
    if not isinstance(c.get("schema_version"), str) or not SCHEMA_VERSION_RE.match(c.get("schema_version", "0.0")):
        errors.append("schema_version must be major.minor")
    if not isinstance(c.get("version"), str) or not VERSION_RE.match(c.get("version", "0.0.0")):
        errors.append("version must be semver")

    def unique_ids(items: object, label: str) -> None:
        if not isinstance(items, list):
            errors.append(f"{label} must be a list")
            return
        ids = []
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                errors.append(f"{label} entries require id")
            else:
                ids.append(item["id"])
        if len(ids) != len(set(ids)):
            errors.append(f"duplicate {label} id")

    unique_ids(c.get("principles"), "principle")
    unique_ids(c.get("authority_levels"), "authority_level")

    authorities = {x.get("id") for x in c.get("authority_levels", []) if isinstance(x, dict)}
    if "human_owner" not in authorities:
        errors.append("human_owner authority is mandatory")

    rules = c.get("governance_rules", {})
    for key in ["agent_self_approval_for_high_risk", "workflow_self_grant_authority", "unknown_authority_is_allowed", "unverified_amendment_is_effective", "history_rewrite_is_allowed", "production_bypass_is_allowed"]:
        if rules.get(key) is not False:
            errors.append(f"governance rule must be false: {key}")

    lifecycle = c.get("amendment_lifecycle")
    if lifecycle != ["proposed", "reviewed", "approved", "effective", "superseded", "retired"]:
        errors.append("amendment_lifecycle is not canonical")

    emergency = c.get("emergency_protocol", {})
    for key in ["requires_reason", "requires_evidence", "requires_post_event_review", "must_be_time_bounded"]:
        if emergency.get(key) is not True:
            errors.append(f"emergency requirement must be true: {key}")
    if emergency.get("initiator") != "human_owner":
        errors.append("emergency initiator must be human_owner")

    enforcement = c.get("enforcement", {})
    for key in ["contract_is_machine_readable", "validator_is_fail_closed", "ci_gate_required", "release_gate_required_for_production_effect"]:
        if enforcement.get(key) is not True:
            errors.append(f"enforcement requirement must be true: {key}")

    if "amendments" in payload:
        if not isinstance(payload["amendments"], list):
            errors.append("amendments must be a list")
        else:
            amendment_ids = set()
            for amendment in payload["amendments"]:
                if not isinstance(amendment, dict):
                    errors.append("amendment must be an object")
                    continue
                aid = amendment.get("amendment_id")
                if aid in amendment_ids:
                    errors.append(f"duplicate amendment_id: {aid}")
                amendment_ids.add(aid)
                for key in c.get("amendment_requirements", {}).get("required_fields", []):
                    if key not in amendment:
                        errors.append(f"amendment {aid} missing required field: {key}")
                if not VERSION_RE.match(str(amendment.get("base_version", ""))):
                    errors.append(f"amendment {aid} base_version must be semver")
                if not VERSION_RE.match(str(amendment.get("target_version", ""))):
                    errors.append(f"amendment {aid} target_version must be semver")
                for key in ["proposed_at", "effective_at"]:
                    if not TIMESTAMP_RE.match(str(amendment.get(key, ""))):
                        errors.append(f"amendment {aid} {key} must be UTC ISO8601")
                approval = amendment.get("approval", {})
                if approval.get("authority") != "human_owner" or approval.get("status") != "approved":
                    errors.append(f"amendment {aid} requires human_owner approved authority")
                if not amendment.get("evidence_ids"):
                    errors.append(f"amendment {aid} requires evidence_ids")

    return errors


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--constitution", type=Path, default=CONSTITUTION)
    parser.add_argument("--fixture", type=Path, default=None)
    args = parser.parse_args()
    constitution_path = args.constitution if args.constitution.is_absolute() else (Path.cwd() / args.constitution).resolve()
    fixture_path = None if args.fixture is None else (args.fixture if args.fixture.is_absolute() else (Path.cwd() / args.fixture).resolve())
    errors = validate(constitution_path)
    if fixture_path:
        errors.extend(validate(fixture_path))
    report = {"status": "PASS" if not errors else "FAIL", "constitution": display_path(constitution_path), "errors": errors}
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
