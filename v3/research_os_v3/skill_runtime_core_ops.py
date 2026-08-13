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
    def _owner_analysis(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        value = str(args.get("text", text))
        words = re.findall(r"[\w\u0E00-\u0E7F]+", value, flags=re.UNICODE)
        raw_constraints = args.get("constraints", [])
        constraints = [str(item) for item in raw_constraints] if isinstance(raw_constraints, list) else []
        return {
            "summary": value.strip(),
            "characters": len(value),
            "words": len(words),
            "constraints": constraints,
            "questions": value.count("?") + value.count("ไหม"),
            "owner_scope": context.user_id,
        }

    @staticmethod
    def _owner_planning(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        goal = str(args.get("goal", text)).strip()
        tasks = max(1, int(args.get("tasks", 1)))
        factory = context.factory_plan(tasks) if context.factory_plan else {"tasks": tasks}
        return {
            "goal": goal,
            "steps": ["understand", "plan", "execute", "validate", "record-evidence"],
            "factory": factory,
            "single_authority": True,
        }

    def _owner_coding(self, name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        query = str(args.get("query", text)).strip()
        matches = self._search_workspace(context.repository_root, query, max(1, min(int(args.get("limit", 8)), 20)))
        return {
            "query": query,
            "matches": matches,
            "mutation_performed": False,
            "write_boundary": "governed-tool-execution",
        }

    def _owner_research(self, name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        query = str(args.get("query", text)).strip()
        matches = self._search_workspace(context.repository_root, query, max(1, min(int(args.get("limit", 8)), 20)))
        return {"query": query, "evidence": matches, "source_count": len(matches), "provenance": True}

    @staticmethod
    def _owner_data(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        raw_rows = args.get("rows", [])
        if not isinstance(raw_rows, list):
            raise ValueError("rows must be a list")
        rows = [row for row in raw_rows if isinstance(row, dict)]
        columns = sorted({str(key) for row in rows for key in row})
        numeric_sums: dict[str, float] = {}
        for column in columns:
            values = [row.get(column) for row in rows]
            numbers = [float(value) for value in values if isinstance(value, (int, float)) and not isinstance(value, bool)]
            if numbers:
                numeric_sums[column] = sum(numbers)
        return {"row_count": len(rows), "columns": columns, "numeric_sums": numeric_sums}

    @staticmethod
    def _owner_documents(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        title = str(args.get("title", "Research OS Document")).strip() or "Research OS Document"
        body = str(args.get("body", text)).strip()
        markdown = f"# {title}\n\n{body}\n"
        return {"title": title, "markdown": markdown, "characters": len(markdown), "persisted": False}

    def _owner_automation(self, name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        action = str(args.get("action", "plan")).strip().lower()
        schedule = str(args.get("schedule", "manual")).strip() or "manual"
        instruction = str(args.get("instruction", text)).strip()
        payload = {"schedule": schedule, "instruction": instruction, "status": "planned"}
        if action == "plan":
            return payload
        if action != "register":
            raise ValueError("unsupported automation action")
        self._require_approval(context, "automation:register")
        automation_id = str(args.get("automation_id", "")).strip() or f"auto-{uuid4().hex[:16]}"
        if not _SAFE_ID_RE.fullmatch(automation_id):
            raise ValueError("invalid automation_id")
        payload.update({"automation_id": automation_id, "status": "registered"})
        self._atomic_json(context.user_data_root / "automation" / f"{automation_id}.json", payload)
        return payload

    @staticmethod
    def _owner_memory(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        action = str(args.get("action", "search")).strip().lower()
        if action == "search":
            if context.memory_search is None:
                raise RuntimeError("memory search runtime is unavailable")
            query = str(args.get("query", text)).strip()
            limit = max(1, min(int(args.get("limit", 8)), 50))
            return {"action": "search", "query": query, "hits": context.memory_search(query, limit)}
        if action == "add":
            if context.memory_add is None:
                raise RuntimeError("memory persistence runtime is unavailable")
            value = str(args.get("text", text)).strip()
            raw_tags = args.get("tags", [])
            tags = tuple(str(item) for item in raw_tags) if isinstance(raw_tags, list) else ()
            return {"action": "add", "memory": context.memory_add(value, tags)}
        raise ValueError("unsupported memory action")

    @staticmethod
    def _owner_security(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        write_requested = bool(args.get("write", False))
        secret_like = sorted(
            str(key)
            for key in args
            if any(token in str(key).lower().replace("-", "_") for token in ("secret", "token", "password", "api_key", "credential"))
        )
        return {
            "owner_scope": context.user_id,
            "write_requested": write_requested,
            "write_allowed": (not write_requested) or context.approved,
            "secret_fields_detected": secret_like,
            "credential_access": False,
        }

    @staticmethod
    def _owner_quality(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        checks = args.get("checks", {})
        if not isinstance(checks, dict):
            raise ValueError("checks must be an object")
        normalized = {str(key): bool(value) for key, value in checks.items()}
        failed = sorted(key for key, value in normalized.items() if not value)
        return {"passed": bool(normalized) and not failed, "checks": normalized, "failed": failed, "evidence_required": True}
