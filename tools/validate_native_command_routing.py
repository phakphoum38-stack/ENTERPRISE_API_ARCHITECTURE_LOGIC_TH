from __future__ import annotations

import json
from pathlib import Path

REQUIRED_RULES = {
    "command_is_not_execution",
    "router_is_not_authority",
    "router_is_not_scheduler",
    "router_is_not_runtime",
    "existing_executor_remains_authoritative",
    "human_authorization_is_required_for_mutation",
    "unknown_capability_is_rejected",
    "unknown_executor_is_rejected",
    "simulation_never_executes",
    "history_is_preserved",
    "provenance_is_preserved",
}
REQUIRED_MODES = {"LIVE", "SIMULATION", "DRY_RUN", "REPLAY"}

def validate(path: Path) -> tuple[str, ...]:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if data.get("status") != "ACTIVE":
        errors.append("contract must be ACTIVE")
    if data.get("initial_action_class") != "READ_ONLY":
        errors.append("initial action class must be READ_ONLY")
    if set(data.get("modes", [])) != REQUIRED_MODES:
        errors.append("mode set mismatch")
    missing = REQUIRED_RULES - set(data.get("rules", []))
    if missing:
        errors.append("missing rules: " + ",".join(sorted(missing)))
    return tuple(errors)

if __name__ == "__main__":
    errors = validate(Path("current/NATIVE_COMMAND_ROUTING_CONTRACT.json"))
    if errors:
        raise SystemExit("\n".join(errors))
