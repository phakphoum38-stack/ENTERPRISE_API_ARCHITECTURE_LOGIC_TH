from __future__ import annotations
from pathlib import Path
from typing import Any
from tools.research_os_code_discovery import discover_code
from tools.research_os_identity_registry import identity_for
from tools.research_os_resource_manifest import ResourceManifest
from tools.research_os_resource_parser import declared_identities

class ResourceBuilder:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def discover(self) -> list[dict[str, Any]]:
        resources = []
        for relative in discover_code(self.root):
            path = self.root / relative
            text = path.read_text(encoding="utf-8", errors="ignore")
            name = Path(relative).name
            kind = (
                "TEST"
                if relative.startswith("tests/")
                or name.startswith("test_")
                else "IMPLEMENTATION"
            )
            identities = declared_identities(relative, text)
            explicit = sorted(
                value
                for value in identities
                if value != Path(relative).stem.lower()
            )
            identity = explicit[0] if explicit else relative
            resource = identity_for(kind, relative, identity)
            resources.append({
                "resource_id": resource.resource_id,
                "kind": resource.kind,
                "path": resource.path,
                "canonical_identity": resource.canonical_identity,
            })
        return resources

    def build(self, existing: ResourceManifest | None = None) -> ResourceManifest:
        manifest = existing or ResourceManifest()
        for resource in self.discover():
            manifest.add(resource)
        return manifest

def build_resources(
    root: str | Path,
    existing: ResourceManifest | None = None,
) -> ResourceManifest:
    return ResourceBuilder(Path(root)).build(existing)
