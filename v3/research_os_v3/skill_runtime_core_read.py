from __future__ import annotations

import re

from .skill_runtime_types import SkillRuntimeContext


class CoreReadSkillHandlers:
    @staticmethod
    def _memory_retrieval(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        if context.memory_search is None:
            raise RuntimeError("memory search runtime is unavailable")
        query = str(args.get("query", text)).strip()
        limit = max(1, min(int(args.get("limit", 8)), 50))
        return {"query": query, "hits": context.memory_search(query, limit)}

    @staticmethod
    def _memory_persistence(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        if context.memory_add is None:
            raise RuntimeError("memory persistence runtime is unavailable")
        value = str(args.get("text", text)).strip()
        raw_tags = args.get("tags", [])
        tags = tuple(str(item) for item in raw_tags) if isinstance(raw_tags, list) else ()
        return {"memory": context.memory_add(value, tags)}

    @staticmethod
    def _conversation_analysis(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        value = str(args.get("text", text))
        words = re.findall(r"[\w\u0E00-\u0E7F]+", value, flags=re.UNICODE)
        return {
            "characters": len(value),
            "words": len(words),
            "lines": 0 if not value else value.count("\n") + 1,
            "code_fences": value.count("```"),
            "has_question": "?" in value or "ไหม" in value or "หรือ" in value,
        }

    @staticmethod
    def _chat_runtime(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        if context.provider_complete is None:
            raise RuntimeError("provider completion runtime is unavailable")
        preferred = str(args.get("preferred_provider", "")).strip() or None
        return context.provider_complete(text, preferred)

    @staticmethod
    def _provider_routing(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        if context.provider_snapshot is None:
            raise RuntimeError("provider status runtime is unavailable")
        providers = context.provider_snapshot()
        ready = [item for item in providers if bool(item.get("ready"))]
        selected = ready[0].get("name") if ready else None
        return {"selected": selected, "providers": providers}

    @staticmethod
    def _agent_routing(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        if context.agent_snapshot is None:
            raise RuntimeError("agent catalog runtime is unavailable")
        agents = context.agent_snapshot()
        requested = str(args.get("agent", "")).strip()
        if requested:
            selected = next((item for item in agents if item.get("name") == requested), None)
            if selected is None:
                raise KeyError(requested)
            return {"selected": selected, "reason": "explicit"}
        haystack = text.lower()
        scored: list[tuple[int, dict[str, object]]] = []
        for agent in agents:
            tokens = {str(agent.get("name", "")).lower(), str(agent.get("role", "")).lower()}
            tokens.update(str(skill).lower() for skill in agent.get("skills", []))
            score = sum(1 for token in tokens if token and token in haystack)
            scored.append((score, agent))
        scored.sort(key=lambda item: (item[0], str(item[1].get("name"))), reverse=True)
        return {"selected": scored[0][1] if scored else None, "reason": "capability-match"}

    @staticmethod
    def _agent_execution(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        if context.agent_run is None:
            raise RuntimeError("agent execution runtime is unavailable")
        agent_name = str(args.get("agent", "researcher")).strip()
        return context.agent_run(agent_name, text)
