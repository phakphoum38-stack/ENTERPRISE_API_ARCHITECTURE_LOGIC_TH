from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from .skills import UnifiedSkillRegistry
from .tools import UnifiedToolRegistry


@dataclass(frozen=True)
class SelfBuildPolicy:
    """Fail-closed policy for creating a Research OS source workspace."""

    include_roots: tuple[str, ...] = (
        "v3",
        "apps/research_os_flutter",
        "owner_special",
        "tools",
        "installer",
        "scripts",
        "docs",
        ".github",
    )
    excluded_parts: tuple[str, ...] = (
        ".git",
        ".dart_tool",
        ".pytest_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
    )
    secret_basenames: tuple[str, ...] = (
        ".env",
        ".env.local",
        "credentials.json",
        "secrets.json",
    )
    secret_suffixes: tuple[str, ...] = (".pfx", ".p12", ".key", ".pem")
    required_paths: tuple[str, ...] = (
        "v3/research_os_v3/orchestrator.py",
        "v3/research_os_v3/skills.py",
        "v3/research_os_v3/tools.py",
        "v3/flutter_app/pubspec.yaml",
        "v3/windows_service/ResearchOS.V3.ServiceHost.csproj",
    )


@dataclass(frozen=True)
class SelfBuildResult:
    workspace: Path
    manifest_path: Path
    file_count: int
    total_bytes: int
    source_tree_sha256: str


class ResearchOSSelfBuilder:
    """Create an isolated, auditable Research OS build workspace.

    This does not mutate the source tree, install software, deploy, or merge.
    Compilation and release actions remain outside this class and are expected
    to run in a bounded CI/sandbox after the staged workspace is validated.
    """

    contract = "research-os-self-build-lab-v1"

    def __init__(self, source_root: Path, policy: SelfBuildPolicy | None = None) -> None:
        self.source_root = source_root.resolve()
        self.policy = policy or SelfBuildPolicy()
        if not self.source_root.is_dir():
            raise FileNotFoundError(self.source_root)

    @staticmethod
    def _sha256_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _allowed(self, relative: Path) -> bool:
        parts = set(relative.parts)
        if parts.intersection(self.policy.excluded_parts):
            return False
        name = relative.name.lower()
        if name in {item.lower() for item in self.policy.secret_basenames}:
            return False
        return not any(name.endswith(suffix.lower()) for suffix in self.policy.secret_suffixes)

    def _iter_source_files(self) -> list[tuple[Path, Path]]:
        selected: list[tuple[Path, Path]] = []
        for root_name in self.policy.include_roots:
            root = (self.source_root / root_name).resolve()
            try:
                root.relative_to(self.source_root)
            except ValueError as exc:
                raise ValueError(f"include root escapes source: {root_name}") from exc
            if not root.exists():
                continue
            if root.is_file():
                candidates = [root]
            else:
                candidates = [path for path in root.rglob("*") if path.is_file()]
            for path in candidates:
                if path.is_symlink():
                    raise ValueError(f"symlink not allowed in self-build input: {path}")
                relative = path.relative_to(self.source_root)
                if self._allowed(relative):
                    selected.append((path, relative))
        selected.sort(key=lambda item: item[1].as_posix())
        return selected

    def capability_snapshot(self) -> dict[str, object]:
        skills = UnifiedSkillRegistry()
        tools = UnifiedToolRegistry()
        discovery = [
            {
                "order": 1,
                "skill": "analysis",
                "action": "understand intent, constraints, and required capability",
            },
            {
                "order": 2,
                "skill": "research",
                "action": "inspect skill/tool registries and available governed integrations",
            },
            {
                "order": 3,
                "skill": "governed-tool-execution",
                "action": "match capability to a native tool and inspect risk metadata",
            },
            {
                "order": 4,
                "skill": "security",
                "action": "check permission and approval requirements before any write",
            },
            {
                "order": 5,
                "tool": "drive-tools-list",
                "action": "when native tools are insufficient, discover checksum-governed packages from the local Drive mirror",
            },
            {
                "order": 6,
                "skill": "planning",
                "action": "compose the smallest bounded execution plan; do not eagerly expand the logical hierarchy",
            },
            {
                "order": 7,
                "skill": "quality",
                "action": "validate result and record evidence before promoting an artifact",
            },
        ]
        return {
            "skills": [
                {
                    "name": item.name,
                    "capability": item.capability,
                    "origin": item.origin.value,
                    "runtime_mode": item.runtime_mode,
                }
                for item in skills.list()
            ],
            "tools": [
                {
                    "name": item.name,
                    "capability": item.capability,
                    "risk": item.risk.value,
                    "approval_required": item.approval_required,
                }
                for item in tools.list()
            ],
            "tool_discovery_process": discovery,
        }

    def stage(self, workspace: Path, *, source_sha: str = "unknown") -> SelfBuildResult:
        workspace = workspace.resolve()
        if workspace == self.source_root:
            raise ValueError("self-build workspace must differ from source root")
        try:
            workspace.relative_to(self.source_root)
        except ValueError:
            pass
        else:
            raise ValueError("self-build workspace must be outside the source tree")
        if workspace.exists():
            raise FileExistsError(workspace)

        files = self._iter_source_files()
        if not files:
            raise RuntimeError("self-build source selection is empty")

        workspace.mkdir(parents=True)
        manifest_files: list[dict[str, object]] = []
        total_bytes = 0
        try:
            for source, relative in files:
                target = workspace / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                size = target.stat().st_size
                total_bytes += size
                manifest_files.append(
                    {
                        "path": relative.as_posix(),
                        "bytes": size,
                        "sha256": self._sha256_file(target),
                    }
                )

            missing = [item for item in self.policy.required_paths if not (workspace / item).is_file()]
            if missing:
                raise RuntimeError(f"self-build workspace missing required paths: {missing}")

            tree_digest = hashlib.sha256()
            for item in manifest_files:
                tree_digest.update(f"{item['path']}:{item['sha256']}\n".encode("utf-8"))
            source_tree_sha256 = tree_digest.hexdigest()

            manifest = {
                "schema_version": 1,
                "contract": self.contract,
                "source_sha": source_sha,
                "source_tree_sha256": source_tree_sha256,
                "file_count": len(manifest_files),
                "total_bytes": total_bytes,
                "policy": {
                    "include_roots": list(self.policy.include_roots),
                    "excluded_parts": list(self.policy.excluded_parts),
                    "secret_basenames": list(self.policy.secret_basenames),
                    "secret_suffixes": list(self.policy.secret_suffixes),
                    "required_paths": list(self.policy.required_paths),
                },
                "capabilities": self.capability_snapshot(),
                "files": manifest_files,
            }
            manifest_path = workspace / "SELF_BUILD_MANIFEST.json"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except Exception:
            shutil.rmtree(workspace, ignore_errors=True)
            raise

        return SelfBuildResult(
            workspace=workspace,
            manifest_path=manifest_path,
            file_count=len(manifest_files),
            total_bytes=total_bytes,
            source_tree_sha256=source_tree_sha256,
        )
