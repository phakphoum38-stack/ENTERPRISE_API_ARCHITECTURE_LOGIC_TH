from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .skill_runtime_core_ops import CoreOpsSkillHandlers
from .skill_runtime_core_read import CoreReadSkillHandlers
from .skill_runtime_legacy_ops import LegacyOpsSkillHandlers
from .skill_runtime_legacy_read import LegacyReadSkillHandlers
from .skill_runtime_types import SkillRuntimeContext
from .skills import UnifiedSkillRegistry

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_TEXT_SUFFIXES = {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".dart", ".ps1", ".sh"}


class NativeSkillRuntime(CoreReadSkillHandlers, CoreOpsSkillHandlers, LegacyReadSkillHandlers, LegacyOpsSkillHandlers):
    """Governed execution surface for every skill in the unified V3 registry."""

    def __init__(self, registry: UnifiedSkillRegistry | None = None) -> None:
        self.registry = registry or UnifiedSkillRegistry()
        self._handlers = {
            "memory-retrieval": self._memory_retrieval,
            "memory-persistence": self._memory_persistence,
            "conversation-analysis": self._conversation_analysis,
            "chat-runtime": self._chat_runtime,
            "provider-routing": self._provider_routing,
            "agent-routing": self._agent_routing,
            "agent-execution": self._agent_execution,
            "durable-orchestration": self._durable_orchestration,
            "workspace-knowledge": self._workspace_knowledge,
            "developer-access": self._developer_access,
            "adaptive-hierarchy": self._adaptive_hierarchy,
            "factory-execution": self._factory_execution,
            "governed-tool-execution": self._governed_tool_execution,
            "provider-resilience": self._provider_readiness,
            "user-isolation": self._user_isolation,
            "analysis": self._owner_tag,
            "planning": self._owner_tag,
            "coding": self._owner_tag,
            "research": self._owner_tag,
            "data": self._owner_tag,
            "documents": self._owner_tag,
            "automation": self._owner_tag,
            "memory": self._owner_tag,
            "security": self._owner_tag,
            "quality": self._owner_tag,
            "research-curation": self._research_curation,
            "knowledge-graph": self._knowledge_graph,
            "house-command-dispatch": self._house_command_dispatch,
            "github-integration": self._github_integration,
            "google-workspace-integration": self._google_workspace_integration,
            "cloud-conversation-sync": self._cloud_conversation_sync,
            "orchestration-observability": self._orchestration_observability,
            "completion-crew": self._completion_crew,
            "quality-gate": self._quality_gate,
            "file-audit-6x6": self._file_audit,
            "developer-identity": self._developer_identity,
            "provider-readiness": self._provider_readiness,
            "owner-policy": self._owner_policy,
            "evidence-recording": self._evidence_recording,
            "v3-bridge": self._v3_bridge,
        }
        missing = sorted(set(item.name for item in self.registry.list()) - set(self._handlers))
        if missing:
            raise ValueError(f"missing V3 skill handlers: {', '.join(missing)}")

    def handler_names(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))

    def execute(
        self,
        name: str,
        text: str = "",
        *,
        arguments: dict[str, object] | None = None,
        context: SkillRuntimeContext,
    ) -> dict[str, object]:
        definition = self.registry.get(name)
        if definition is None:
            raise KeyError(name)
        if definition.runtime_mode != "native" or not definition.native_v3:
            raise RuntimeError(f"skill is not executable in V3: {name}")
        handler = self._handlers[name]
        output = handler(name, text.strip(), dict(arguments or {}), context)
        return {
            "skill": name,
            "origin": definition.origin.value,
            "runtime_mode": definition.runtime_mode,
            "execution_adapter": definition.execution_adapter,
            "source": definition.source,
            "result": output,
        }

    @staticmethod
    def _require_approval(context: SkillRuntimeContext, action: str) -> None:
        if not context.approved:
            raise PermissionError(f"skill action requires approval: {action}")

    @staticmethod
    def _search_workspace(root: Path, query: str, limit: int) -> list[dict[str, object]]:
        wanted = {token.lower() for token in re.findall(r"[\w\u0E00-\u0E7F]+", query, flags=re.UNICODE) if len(token) > 1}
        if not wanted:
            return []
        results: list[tuple[int, dict[str, object]]] = []
        scanned = 0
        for path in sorted(root.rglob("*")):
            if scanned >= 400:
                break
            if not path.is_file() or path.suffix.lower() not in _TEXT_SUFFIXES:
                continue
            rel = path.relative_to(root)
            if any(part in {".git", ".pytest_cache", "build", "dist", "node_modules"} for part in rel.parts):
                continue
            scanned += 1
            try:
                value = path.read_text(encoding="utf-8", errors="ignore")[:65536]
            except OSError:
                continue
            lower = value.lower()
            score = sum(lower.count(token) for token in wanted)
            if score <= 0:
                continue
            first = min((lower.find(token) for token in wanted if token in lower), default=0)
            start = max(0, first - 120)
            excerpt = " ".join(value[start : start + 360].split())
            results.append((score, {"path": rel.as_posix(), "score": score, "excerpt": excerpt}))
        results.sort(key=lambda item: (item[0], item[1]["path"]), reverse=True)
        return [item for _, item in results[:limit]]

    @staticmethod
    def _atomic_json(path: Path, payload: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, path)
