from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Mapping


RESOURCE_TRANSLATOR_SCHEMA = "RESEARCH_OS_CANONICAL_RESOURCE_V1"

VALID_KINDS = frozenset({
    "CONTRACT",
    "IMPLEMENTATION",
    "WORKFLOW",
    "TEST",
    "EVIDENCE",
    "MANIFEST",
    "EXTERNAL_TOOL",
    "PROJECT",
    "CONFIGURATION",
    "DOCUMENT",
    "UNKNOWN",
})


@dataclass(frozen=True)
class CanonicalResource:
    resource_id: str
    kind: str
    path: str
    canonical_identity: str
    schema: str = RESOURCE_TRANSLATOR_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_path(value: str) -> str:
    return value.replace("\\\\", "/").strip()


def normalize_kind(value: str | None) -> str:
    if not value:
        return "UNKNOWN"

    value = value.strip().upper()

    aliases = {
        "CODE": "IMPLEMENTATION",
        "SOURCE": "IMPLEMENTATION",
        "SCRIPT": "IMPLEMENTATION",
        "TESTS": "TEST",
        "TEST_FILE": "TEST",
        "CONTRACTS": "CONTRACT",
        "WORKFLOWS": "WORKFLOW",
        "TOOLS": "EXTERNAL_TOOL",
    }

    value = aliases.get(value, value)

    return value if value in VALID_KINDS else "UNKNOWN"


def normalize_identity(value: str | None, path: str) -> str:
    if value and value.strip():
        return value.strip().lower()

    return Path(path).stem.lower()


def translate_resource(
    resource: Mapping[str, Any],
) -> CanonicalResource:
    path = normalize_path(str(resource.get("path", "")))

    if not path:
        raise ValueError("RESOURCE_PATH_REQUIRED")

    resource_id = str(resource.get("resource_id", "")).strip()

    if not resource_id:
        raise ValueError("RESOURCE_ID_REQUIRED")

    kind = normalize_kind(
        str(resource.get("kind", "")) or None
    )

    identity = normalize_identity(
        resource.get("canonical_identity"),
        path,
    )

    return CanonicalResource(
        resource_id=resource_id,
        kind=kind,
        path=path,
        canonical_identity=identity,
    )


def translate_resources(
    resources: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    translated = [
        translate_resource(resource).to_dict()
        for resource in resources
    ]

    translated.sort(
        key=lambda x: (
            x["kind"],
            x["path"],
            x["resource_id"],
        )
    )

    return translated
