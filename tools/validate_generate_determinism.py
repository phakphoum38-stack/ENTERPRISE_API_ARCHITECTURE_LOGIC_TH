"""Validate deterministic Generate inputs used by the orchestrator.

This is an input/canonicalization gate only.  It does not execute workflows,
create branches, call GitHub, or mutate repository state.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "current" / "GENERATE_WORKFLOW_REGISTRY.yml"
TOOL_REGISTRY = ROOT / "current" / "tools" / "generate-tool-registry.yml"
SKILL_MEMORY = ROOT / "current" / "GENERATE_SKILL_MEMORY.md"
MAX_BYTES = 64 * 1024
MAX_STAGES = 100
MAX_TOOLS = 100


def _read_bounded(path: Path) -> bytes:
    data = path.read_bytes()
    if not data:
        raise AssertionError(f"required Generate input is empty: {path}")
    if len(data) > MAX_BYTES:
        raise AssertionError(f"Generate input exceeds {MAX_BYTES} bytes: {path}")
    return data


def _canonical_yaml(path: Path) -> tuple[bytes, Any]:
    raw = _read_bounded(path)
    text = raw.decode("utf-8")
    value = yaml.safe_load(text)
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return canonical, value


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _validate_registry(registry: Any) -> None:
    assert isinstance(registry, dict), "Generate workflow registry must be a mapping"
    stages = registry.get("stages")
    assert isinstance(stages, list) and stages, "Generate workflow registry stages must not be empty"
    assert len(stages) <= MAX_STAGES, "Generate workflow registry has too many stages"

    stage_ids: list[int] = []
    dispatchable: list[tuple[int, str]] = []
    for entry in stages:
        assert isinstance(entry, dict), f"invalid Generate stage: {entry!r}"
        stage = int(entry["stage"])
        workflow = entry.get("file")
        assert isinstance(workflow, str) and workflow, f"invalid Generate workflow: {entry!r}"
        stage_ids.append(stage)
        if entry.get("dispatchable") is True:
            dispatchable.append((stage, workflow))

    assert stage_ids == sorted(stage_ids), "Generate stages must be ordered"
    assert len(stage_ids) == len(set(stage_ids)), "Generate stages must be unique"
    assert dispatchable == sorted(dispatchable), "dispatchable Generate stages must be ordered"


def _validate_tool_registry(tools: Any) -> None:
    assert isinstance(tools, dict), "Generate tool registry must be a mapping"
    entries = tools.get("entries")
    assert isinstance(entries, list) and entries, "Generate tool registry must not be empty"
    assert len(entries) <= MAX_TOOLS, "Generate tool registry has too many entries"

    ids: list[str] = []
    for entry in entries:
        assert isinstance(entry, dict), f"invalid Generate tool entry: {entry!r}"
        for field in ("id", "capability", "safe_boundary"):
            assert isinstance(entry.get(field), str) and entry[field], (
                f"Generate tool entry missing {field}: {entry!r}"
            )
        ids.append(entry["id"])

    assert ids == sorted(ids), "Generate tool registry entries must be ordered by id"
    assert len(ids) == len(set(ids)), "Generate tool ids must be unique"


def _validate_skill_memory(data: bytes) -> None:
    text = data.decode("utf-8")
    required = ("candidate", "validated", "reusable", "Evidence")
    for marker in required:
        assert marker in text, f"Skill memory contract missing: {marker}"


def main() -> None:
    registry_canonical, registry = _canonical_yaml(REGISTRY)
    tools_canonical, tools = _canonical_yaml(TOOL_REGISTRY)
    memory_raw = _read_bounded(SKILL_MEMORY)

    _validate_registry(registry)
    _validate_tool_registry(tools)
    _validate_skill_memory(memory_raw)

    # Re-serializing parsed YAML must produce the same canonical bytes. This
    # makes the gate insensitive to YAML formatting while remaining strict
    # about the semantic input consumed by Generate.
    registry_again = json.dumps(
        yaml.safe_load(REGISTRY.read_text(encoding="utf-8")),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    tools_again = json.dumps(
        yaml.safe_load(TOOL_REGISTRY.read_text(encoding="utf-8")),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert registry_canonical == registry_again, "Generate registry canonicalization is unstable"
    assert tools_canonical == tools_again, "Generate tool registry canonicalization is unstable"

    print("Generate determinism validation passed: canonical inputs are stable.")
    print(f"Workflow registry SHA256: {_sha256(registry_canonical)}")
    print(f"Tool registry SHA256: {_sha256(tools_canonical)}")
    print(f"Skill Memory SHA256: {_sha256(memory_raw)}")


if __name__ == "__main__":
    main()
