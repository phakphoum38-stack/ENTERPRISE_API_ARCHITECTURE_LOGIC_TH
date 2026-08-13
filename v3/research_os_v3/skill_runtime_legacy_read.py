from __future__ import annotations

import ast
import hashlib
from .skill_runtime_types import SkillRuntimeContext


class LegacyReadSkillHandlers:
    def _research_curation(self, name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        query = str(args.get("query", text)).strip()
        matches = self._search_workspace(context.repository_root, query, max(1, min(int(args.get("limit", 8)), 20)))
        for item in matches:
            material = f"{item['path']}\n{item['excerpt']}".encode("utf-8", errors="ignore")
            item["provenance_sha256"] = hashlib.sha256(material).hexdigest()
        return {"query": query, "curated": matches, "provenance": True}

    @staticmethod
    def _knowledge_graph(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        limit = max(1, min(int(args.get("limit", 80)), 200))
        nodes: set[str] = set()
        edges: list[dict[str, str]] = []
        for path in sorted(context.repository_root.rglob("*.py"))[:limit]:
            if any(part.startswith(".") for part in path.relative_to(context.repository_root).parts):
                continue
            rel = path.relative_to(context.repository_root).as_posix()
            nodes.add(rel)
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore")[:131072])
            except (OSError, SyntaxError):
                continue
            for item in ast.walk(tree):
                if isinstance(item, ast.Import):
                    for alias in item.names:
                        edges.append({"from": rel, "to": alias.name, "type": "import"})
                elif isinstance(item, ast.ImportFrom) and item.module:
                    edges.append({"from": rel, "to": item.module, "type": "import"})
        return {"nodes": sorted(nodes), "edges": edges[:500], "truncated": len(edges) > 500}

    def _house_command_dispatch(self, name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        action = str(args.get("action", "status")).strip().lower()
        if action == "status":
            return {"status": "ready", "allowed_actions": ["status", "echo"], "single_authority": True}
        if action != "echo":
            raise ValueError("house command is not allowlisted")
        self._require_approval(context, "house-command:echo")
        return {"action": "echo", "text": str(args.get("text", text))}

    @staticmethod
    def _github_integration(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        head = context.repository_root / ".git" / "HEAD"
        branch = None
        if head.exists():
            raw = head.read_text(encoding="utf-8", errors="ignore").strip()
            branch = raw.removeprefix("ref: refs/heads/") if raw.startswith("ref: refs/heads/") else raw[:12]
        return {
            "repository_root": str(context.repository_root),
            "branch": branch,
            "boundary": "governed-external-connector",
            "credential_access": False,
        }

    @staticmethod
    def _google_workspace_integration(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        return {
            "boundary": "owner-authorized-external-connector",
            "credential_access": False,
            "single_authority": True,
        }
