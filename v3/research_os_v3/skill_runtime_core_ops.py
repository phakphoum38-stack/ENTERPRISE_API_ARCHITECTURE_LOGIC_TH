from __future__ import annotations

import json
import re
from uuid import uuid4

from .skill_runtime_types import SkillRuntimeContext

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class CoreOpsSkillHandlers:
    def _durable_orchestration(self, name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        root = context.user_data_root / "orchestration"
        root.mkdir(parents=True, exist_ok=True)
        action = str(args.get("action", "create")).strip().lower()
        run_id = str(args.get("run_id", "")).strip()
        if action == "create":
            self._require_approval(context, action)
            run_id = run_id or f"v3run-{uuid4().hex[:16]}"
            if not _SAFE_ID_RE.fullmatch(run_id):
                raise ValueError("invalid run_id")
            tasks = max(1, int(args.get("tasks", 1)))
            plan = context.factory_plan(tasks) if context.factory_plan else {"tasks": tasks}
            payload = {"run_id": run_id, "status": "planned", "prompt": text, "plan": plan, "attempt": 1}
            self._atomic_json(root / f"{run_id}.json", payload)
            return payload
        if not run_id or not _SAFE_ID_RE.fullmatch(run_id):
            raise ValueError("run_id is required")
        path = root / f"{run_id}.json"
        if not path.exists():
            raise KeyError(run_id)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if action == "status":
            return payload
        if action not in {"resume", "retry", "cancel"}:
            raise ValueError("unsupported orchestration action")
        self._require_approval(context, action)
        payload["status"] = {"resume": "planned", "retry": "planned", "cancel": "cancelled"}[action]
        if action == "retry":
            payload["attempt"] = int(payload.get("attempt", 1)) + 1
        self._atomic_json(path, payload)
        return payload

    def _workspace_knowledge(self, name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        query = str(args.get("query", text)).strip()
        limit = max(1, min(int(args.get("limit", 10)), 25))
        return {"query": query, "matches": self._search_workspace(context.repository_root, query, limit)}

    @staticmethod
    def _developer_access(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        role = str(args.get("role", "developer")).strip().lower()
        owner_approved = bool(args.get("owner_approved", False))
        trial = bool(args.get("trial", False))
        allowed = role in {"viewer", "developer"} and (role == "viewer" or owner_approved)
        return {
            "role": role,
            "allowed": allowed,
            "owner_approval_required": role == "developer",
            "trial_isolated": trial,
            "user_scope": f"{context.user_id}/{context.profile_id}",
        }

    @staticmethod
    def _adaptive_hierarchy(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        if context.factory_plan is None:
            raise RuntimeError("factory planner runtime is unavailable")
        tasks = max(1, int(args.get("tasks", 1)))
        return context.factory_plan(tasks)

    @staticmethod
    def _factory_execution(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        if context.factory_plan is None:
            raise RuntimeError("factory runtime is unavailable")
        tasks = max(1, int(args.get("tasks", 1)))
        result = context.factory_plan(tasks)
        return {**result, "execution_boundary": "use UnifiedMasterOrchestrator.execute_factory for stage execution"}

    @staticmethod
    def _governed_tool_execution(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        if context.tool_run is None:
            raise RuntimeError("tool execution runtime is unavailable")
        tool_name = str(args.get("tool", "echo")).strip()
        raw = args.get("arguments", {"text": text})
        if not isinstance(raw, dict):
            raise ValueError("tool arguments must be an object")
        return context.tool_run(tool_name, dict(raw), context.approved)

    @staticmethod
    def _user_isolation(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        return {
            "user_id": context.user_id,
            "profile_id": context.profile_id,
            "scope": str(context.user_data_root),
            "isolated": True,
        }

    @staticmethod
    def _owner_tag(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        return {"text": f"{name}: {text.strip()}", "owner_scope": context.user_id}
