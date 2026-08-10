from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


class OwnerBundleBuilder:
    """Build a portable source bundle containing only owned architecture files."""

    INCLUDED_ROOT_FILES = ("OWNER_MANIFEST.json", "README.md", "pyproject.toml")

    def __init__(self, owner_special_root: Path) -> None:
        self.root = Path(owner_special_root).resolve()

    @staticmethod
    def _sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _source_files(self) -> list[Path]:
        files = [self.root / name for name in self.INCLUDED_ROOT_FILES]
        files.extend(sorted((self.root / "research_os_friend").glob("*.py")))
        files.extend(sorted((self.root / "scripts").glob("*.py")))
        files.extend(sorted((self.root / "tests").glob("*.py")))
        return [path for path in files if path.is_file()]

    def build(self, destination: Path) -> dict[str, object]:
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        inventory: list[dict[str, object]] = []
        payloads: list[tuple[str, bytes]] = []
        for path in self._source_files():
            relative = path.relative_to(self.root).as_posix()
            data = path.read_bytes()
            payloads.append((relative, data))
            inventory.append({"path": relative, "sha256": self._sha256(data), "bytes": len(data)})

        bundle_manifest = {
            "schema_version": 1,
            "edition": "owner-special",
            "bundle": "Friend Complete",
            "content_policy": "source and architecture files only; runtime owner data is external",
            "files": inventory,
        }
        manifest_bytes = (json.dumps(bundle_manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")

        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for relative, data in payloads:
                info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, data)
            info = zipfile.ZipInfo("BUNDLE_MANIFEST.json", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, manifest_bytes)

        return {
            "path": str(destination),
            "sha256": self._sha256(destination.read_bytes()),
            "files": len(inventory) + 1,
            "source_only": True,
        }
