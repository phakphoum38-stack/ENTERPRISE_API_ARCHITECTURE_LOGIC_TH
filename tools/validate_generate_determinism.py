from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "current" / "GENERATE_WORKFLOW_REGISTRY.yml"
TOOL_REGISTRY = ROOT / "current" / "tools" / "generate-tool-registry.yml"

# Runtime/run metadata must never participate in generation inputs. If a future
# generator needs such metadata, it must keep it outside the deterministic input
# contract and outside the generated artifact payload.
VOLATILE_KEYS = {
    "created_at",
    "generated_at",
    "timestamp",
    "run_id",
    "workflow_run_id",
    "random",
    "nonce",
    "uuid",
}


def _load(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _assert_no_volatile_keys(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().lower()
            if normalized in VOLATILE_KEYS:
                raise SystemExit(
                    f"Non-deterministic generation input detected: {path}.{key}"
                )
            _assert_no_volatile_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_volatile_keys(child, f"{path}[{index}]")


def _canonical_bytes(value: Any) -> bytes:
    # JSON gives us a stable representation independent of YAML whitespace,
    # comments, and mapping formatting. Mapping keys are sorted recursively.
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        .encode("utf-8")
    )


def _fingerprint() -> str:
    registry = _load(REGISTRY)
    tool_registry = _load(TOOL_REGISTRY)
    _assert_no_volatile_keys(registry, "GENERATE_WORKFLOW_REGISTRY")
    _assert_no_volatile_keys(tool_registry, "generate-tool-registry")
    payload = {
        "workflow_registry": registry,
        "tool_registry": tool_registry,
    }
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def main() -> None:
    first = _fingerprint()
    second = _fingerprint()
    if first != second:
        raise SystemExit(
            "Deterministic generation input contract failed: repeated fingerprints differ."
        )
    print(f"Deterministic generation input contract passed: {first}")
    print(
        "Note: this gate proves deterministic generation inputs/canonicalization; "
        "a future generator-output regression gate must additionally compare generated artifacts."
    )


if __name__ == "__main__":
    main()
