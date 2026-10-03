from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Iterable
import hashlib
import json

@dataclass
class ResourceManifest:
    schema: str = "RESEARCH_OS_RESOURCE_MANIFEST_V1"
    source_sha256: str = ""
    resources: list[dict[str, Any]] = field(default_factory=list)

    def add(self, resource: dict[str, Any]) -> None:
        resource_id = resource.get("resource_id")
        if not resource_id:
            raise ValueError("resource_id required")
        candidate = dict(resource)

        for existing in self.resources:
            if existing.get("resource_id") != resource_id:
                continue

            if existing == candidate:
                return

            raise ValueError(
                f"RESOURCE_ID_COLLISION:{resource_id}"
            )

        self.resources.append(candidate)

    def canonical(self) -> str:
        payload = asdict(self)
        payload["resources"] = sorted(
            payload["resources"],
            key=lambda x: (
                x.get("kind", ""),
                x.get("path", ""),
                x.get("resource_id", ""),
            ),
        )
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def sha256(self) -> str:
        return hashlib.sha256(self.canonical().encode()).hexdigest()

def build_manifest(
    source_sha256: str,
    resources: Iterable[dict[str, Any]],
) -> ResourceManifest:
    manifest = ResourceManifest(source_sha256=source_sha256)
    for resource in resources:
        manifest.add(resource)
    return manifest
