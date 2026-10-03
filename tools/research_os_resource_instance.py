from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


RESOURCE_INSTANCE_SCHEMA = "RESEARCH_OS_RESOURCE_INSTANCE_V1"


def normalize_path(path: str | Path) -> str:
    value = str(path).replace("\\", "/").strip()
    if not value:
        raise ValueError("RESOURCE_INSTANCE_PATH_REQUIRED")
    return value


def normalize_resource_id(resource_id: str) -> str:
    value = str(resource_id).strip()
    if not value:
        raise ValueError("RESOURCE_INSTANCE_RESOURCE_ID_REQUIRED")
    return value


def content_fingerprint(content: bytes) -> str:
    if not isinstance(content, bytes):
        raise TypeError("RESOURCE_INSTANCE_CONTENT_MUST_BE_BYTES")
    return hashlib.sha256(content).hexdigest()


def instance_fingerprint(
    resource_id: str,
    path: str,
    content_sha256: str,
) -> str:
    resource_id = normalize_resource_id(resource_id)
    path = normalize_path(path)

    if not content_sha256:
        raise ValueError("RESOURCE_INSTANCE_CONTENT_SHA256_REQUIRED")

    payload = {
        "resource_id": resource_id,
        "path": path,
        "content_sha256": content_sha256,
    }

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class ResourceInstance:
    resource_id: str
    path: str
    content_sha256: str
    instance_sha256: str

    @classmethod
    def create(
        cls,
        resource_id: str,
        path: str,
        content: bytes,
    ) -> "ResourceInstance":
        resource_id = normalize_resource_id(resource_id)
        path = normalize_path(path)

        content_sha = content_fingerprint(content)
        instance_sha = instance_fingerprint(
            resource_id,
            path,
            content_sha,
        )

        return cls(
            resource_id=resource_id,
            path=path,
            content_sha256=content_sha,
            instance_sha256=instance_sha,
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "schema": RESOURCE_INSTANCE_SCHEMA,
            "resource_id": self.resource_id,
            "path": self.path,
            "content_sha256": self.content_sha256,
            "instance_sha256": self.instance_sha256,
        }


def instance_from_file(
    resource_id: str,
    path: str | Path,
) -> ResourceInstance:
    normalized = normalize_path(path)
    source = Path(path)

    if not source.is_file():
        raise FileNotFoundError(
            f"RESOURCE_INSTANCE_FILE_NOT_FOUND:{normalized}"
        )

    return ResourceInstance.create(
        resource_id=resource_id,
        path=normalized,
        content=source.read_bytes(),
    )
