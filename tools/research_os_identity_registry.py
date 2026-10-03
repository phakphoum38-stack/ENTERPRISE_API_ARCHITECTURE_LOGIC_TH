from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib
from typing import Iterable

@dataclass(frozen=True)
class ResourceIdentity:
    resource_id: str
    kind: str
    path: str
    canonical_identity: str

def make_resource_id(kind: str, identity: str) -> str:
    key = f"{kind.upper()}:{identity.strip().lower()}".encode()
    return hashlib.sha256(key).hexdigest()[:24]

def identity_for(kind: str, path: str, identity: str | None = None) -> ResourceIdentity:
    canonical = (identity or path).strip().lower()
    return ResourceIdentity(
        make_resource_id(kind, canonical),
        kind.upper(),
        path.replace("\\", "/"),
        canonical,
    )

def index(resources: Iterable[ResourceIdentity]) -> dict[str, ResourceIdentity]:
    result = {}
    for resource in resources:
        previous = result.get(resource.resource_id)
        if previous is not None and previous != resource:
            raise ValueError(f"RESOURCE_ID_COLLISION:{resource.resource_id}")
        result[resource.resource_id] = resource
    return result

def to_dict(resource: ResourceIdentity) -> dict:
    return asdict(resource)
