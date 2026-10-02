from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from tools.research_os_resource_instance import ResourceInstance


RESOURCE_DRIFT_SCHEMA = "RESEARCH_OS_RESOURCE_DRIFT_V1"


DRIFT_STATES = frozenset(
    {
        "UNCHANGED",
        "CONTENT_DRIFT",
        "PATH_DRIFT",
        "RESOURCE_ID_DRIFT",
        "ADDED",
        "REMOVED",
    }
)


def _value(mapping: Mapping, key: str) -> str:
    value = mapping.get(key)
    if value is None:
        raise ValueError(f"RESOURCE_DRIFT_FIELD_REQUIRED:{key}")

    value = str(value).strip()
    if not value:
        raise ValueError(f"RESOURCE_DRIFT_FIELD_REQUIRED:{key}")

    return value


def _instance_fields(instance: ResourceInstance) -> tuple[str, str, str]:
    return (
        _value(instance.to_dict(), "resource_id"),
        _value(instance.to_dict(), "path"),
        _value(instance.to_dict(), "content_sha256"),
    )


@dataclass(frozen=True)
class ResourceDrift:
    resource_id: str
    state: str
    baseline_path: str | None
    current_path: str | None
    baseline_content_sha256: str | None
    current_content_sha256: str | None

    def to_dict(self) -> dict:
        if self.state not in DRIFT_STATES:
            raise ValueError(
                f"RESOURCE_DRIFT_INVALID_STATE:{self.state}"
            )

        return {
            "schema": RESOURCE_DRIFT_SCHEMA,
            "resource_id": self.resource_id,
            "state": self.state,
            "baseline_path": self.baseline_path,
            "current_path": self.current_path,
            "baseline_content_sha256": self.baseline_content_sha256,
            "current_content_sha256": self.current_content_sha256,
        }


def compare_instances(
    baseline: ResourceInstance,
    current: ResourceInstance,
) -> ResourceDrift:
    baseline_id, baseline_path, baseline_sha = _instance_fields(baseline)
    current_id, current_path, current_sha = _instance_fields(current)

    if baseline_id != current_id:
        state = "RESOURCE_ID_DRIFT"
    elif baseline_path != current_path:
        state = "PATH_DRIFT"
    elif baseline_sha != current_sha:
        state = "CONTENT_DRIFT"
    else:
        state = "UNCHANGED"

    return ResourceDrift(
        resource_id=current_id,
        state=state,
        baseline_path=baseline_path,
        current_path=current_path,
        baseline_content_sha256=baseline_sha,
        current_content_sha256=current_sha,
    )


def compare_resource_sets(
    baseline: Mapping[str, ResourceInstance],
    current: Mapping[str, ResourceInstance],
) -> list[ResourceDrift]:
    baseline_ids = set(baseline)
    current_ids = set(current)

    results: list[ResourceDrift] = []

    for resource_id in sorted(current_ids - baseline_ids):
        instance = current[resource_id]
        _, path, sha = _instance_fields(instance)
        results.append(
            ResourceDrift(
                resource_id=resource_id,
                state="ADDED",
                baseline_path=None,
                current_path=path,
                baseline_content_sha256=None,
                current_content_sha256=sha,
            )
        )

    for resource_id in sorted(baseline_ids - current_ids):
        instance = baseline[resource_id]
        _, path, sha = _instance_fields(instance)
        results.append(
            ResourceDrift(
                resource_id=resource_id,
                state="REMOVED",
                baseline_path=path,
                current_path=None,
                baseline_content_sha256=sha,
                current_content_sha256=None,
            )
        )

    for resource_id in sorted(baseline_ids & current_ids):
        results.append(
            compare_instances(
                baseline[resource_id],
                current[resource_id],
            )
        )

    return sorted(
        results,
        key=lambda item: item.resource_id,
    )



def compare_resource_changes(
    baseline: Mapping[str, ResourceInstance],
    changes: Iterable[Mapping],
) -> list[ResourceDrift]:
    """Compare only resources affected by an incremental change batch.

    The change records are produced by the incremental resource processor.
    No repository scan is performed here. Resource identity remains external
    to this function and DELETE records must carry a known baseline identity.
    """

    results: list[ResourceDrift] = []

    for change in changes:
        if not isinstance(change, Mapping):
            raise TypeError("RESOURCE_DRIFT_CHANGE_MAPPING_REQUIRED")

        resource_id = _value(change, "resource_id")
        operation = _value(change, "operation").upper()

        if operation == "DELETE":
            if resource_id not in baseline:
                raise ValueError(
                    f"RESOURCE_DRIFT_DELETE_BASELINE_REQUIRED:{resource_id}"
                )

            baseline_id, baseline_path, baseline_sha = _instance_fields(
                baseline[resource_id]
            )

            results.append(
                ResourceDrift(
                    resource_id=baseline_id,
                    state="REMOVED",
                    baseline_path=baseline_path,
                    current_path=None,
                    baseline_content_sha256=baseline_sha,
                    current_content_sha256=None,
                )
            )
            continue

        instance = change.get("instance")

        if not isinstance(instance, ResourceInstance):
            raise TypeError(
                f"RESOURCE_DRIFT_INSTANCE_REQUIRED:{resource_id}"
            )

        if instance.resource_id != resource_id:
            raise ValueError(
                f"RESOURCE_DRIFT_RESOURCE_ID_MISMATCH:{resource_id}"
            )

        if resource_id not in baseline:
            _, path, sha = _instance_fields(instance)

            results.append(
                ResourceDrift(
                    resource_id=resource_id,
                    state="ADDED",
                    baseline_path=None,
                    current_path=path,
                    baseline_content_sha256=None,
                    current_content_sha256=sha,
                )
            )
            continue

        results.append(
            compare_instances(
                baseline[resource_id],
                instance,
            )
        )

    return sorted(
        results,
        key=lambda item: item.resource_id,
    )


def diff_paths(
    previous: Iterable[str],
    current: Iterable[str],
) -> dict[str, list[str]]:
    old = {str(value).replace("\\", "/") for value in previous}
    new = {str(value).replace("\\", "/") for value in current}

    return {
        "added": sorted(new - old),
        "removed": sorted(old - new),
        "unchanged": sorted(old & new),
    }


def resource_changed(old: Mapping, new: Mapping) -> bool:
    old_sha = old.get("content_sha256", old.get("sha256"))
    new_sha = new.get("content_sha256", new.get("sha256"))

    old_identity = old.get("resource_id", old.get("canonical_identity"))
    new_identity = new.get("resource_id", new.get("canonical_identity"))

    return old_sha != new_sha or old_identity != new_identity


def detect_orphans(
    manifest_paths: Iterable[str],
    actual_paths: Iterable[str],
) -> dict[str, list[str]]:
    return diff_paths(manifest_paths, actual_paths)
