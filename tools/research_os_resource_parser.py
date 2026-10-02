from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

IDENTITY_FIELDS = (
    "contract",
    "contract_id",
    "capability_id",
    "component_id",
    "resource_id",
)

VALUE_RE = re.compile(
    r'''^\s*(?:contract|contract_id|capability_id|component_id|resource_id)\s*:\s*(?:"([^"]+)"|'([^']+)'|([^#\s]+))\s*(?:#.*)?$''',
    re.IGNORECASE | re.MULTILINE,
)

def normalize_path(value: str) -> str:
    return value.replace("\\", "/").strip()

def normalize_identity(value: str) -> str:
    return value.strip().strip(chr(34)).strip(chr(39)).lower()

def parse_json(text: str) -> dict[str, Any] | None:
    try:
        value = json.loads(text)
    except (TypeError, ValueError):
        return None
    return value if isinstance(value, dict) else None

def explicit_identities(path: str, text: str) -> set[str]:
    values: set[str] = set()
    obj = parse_json(text)
    if obj:
        for field in IDENTITY_FIELDS:
            value = obj.get(field)
            if isinstance(value, str) and value.strip():
                values.add(normalize_identity(value))

    # YAML-style identity declarations are only valid for
    # YAML/YML resources. Never apply this grammar to Python,
    # PowerShell, Dart, JS, or other programming languages because
    # constructs such as `resource_id: str` are type annotations,
    # not resource identities.
    suffix = Path(path).suffix.lower()

    if suffix in {".yaml", ".yml"}:
        for match in VALUE_RE.finditer(text):
            value = next(
                (x for x in match.groups() if x is not None),
                None,
            )
            if value:
                values.add(normalize_identity(value))

    return values

def declared_identities(path: str, text: str) -> set[str]:
    values = explicit_identities(path, text)
    values.add(Path(path).stem.lower())
    return values

def structured_bindings(text: str) -> dict[str, Any] | None:
    obj = parse_json(text)
    if not obj:
        return None
    for key in (
        "bindings",
        "semantic_bindings",
        "relationships",
    ):
        value = obj.get(key)
        if isinstance(value, dict):
            return value
    return None
