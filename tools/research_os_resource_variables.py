from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping

RESOURCE_VARIABLE_SCHEMA = "RESEARCH_OS_RESOURCE_VARIABLE_V1"

VALID_TYPES = frozenset({
    "STRING",
    "INTEGER",
    "NUMBER",
    "BOOLEAN",
    "PATH",
    "IDENTITY",
    "RESOURCE_ID",
    "JSON",
})


@dataclass(frozen=True)
class ResourceVariable:
    name: str
    type: str
    value: Any = None
    source: str = "declared"
    required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_name(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("RESOURCE_VARIABLE_NAME_REQUIRED")
    return value


def normalize_type(value: str) -> str:
    normalized = value.strip().upper()
    if normalized not in VALID_TYPES:
        raise ValueError(
            f"INVALID_RESOURCE_VARIABLE_TYPE:{value}"
        )
    return normalized


def create_variable(
    name: str,
    variable_type: str,
    value: Any = None,
    source: str = "declared",
    required: bool = False,
) -> ResourceVariable:
    name = normalize_name(name)
    variable_type = normalize_type(variable_type)

    if required and value is None:
        raise ValueError(
            f"REQUIRED_RESOURCE_VARIABLE_MISSING:{name}"
        )

    return ResourceVariable(
        name=name,
        type=variable_type,
        value=value,
        source=source.strip() or "declared",
        required=bool(required),
    )


def variables_from_mapping(
    values: Mapping[str, Mapping[str, Any]],
) -> list[ResourceVariable]:
    result = []

    for name, definition in values.items():
        if not isinstance(definition, Mapping):
            raise ValueError(
                f"INVALID_RESOURCE_VARIABLE:{name}"
            )

        result.append(
            create_variable(
                name,
                str(definition.get("type", "STRING")),
                definition.get("value"),
                str(definition.get("source", "declared")),
                bool(definition.get("required", False)),
            )
        )

    return validate_variables(result)


def validate_variables(
    variables: list[ResourceVariable],
) -> list[ResourceVariable]:
    seen = set()

    for variable in variables:
        if variable.name in seen:
            raise ValueError(
                f"DUPLICATE_RESOURCE_VARIABLE:{variable.name}"
            )

        seen.add(variable.name)

        if variable.type not in VALID_TYPES:
            raise ValueError(
                f"INVALID_RESOURCE_VARIABLE_TYPE:{variable.type}"
            )

        if variable.required and variable.value is None:
            raise ValueError(
                f"REQUIRED_RESOURCE_VARIABLE_MISSING:{variable.name}"
            )

    return sorted(variables, key=lambda x: x.name)


def variable_dict(
    variable: ResourceVariable,
) -> dict[str, Any]:
    return variable.to_dict()
