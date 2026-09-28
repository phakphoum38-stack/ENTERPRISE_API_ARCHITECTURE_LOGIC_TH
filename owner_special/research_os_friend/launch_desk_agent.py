from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

from .launch_desk import build_deterministic_plan, launch_desk_tool_map

INSTRUCTIONS = """You are Launch Desk, the Research OS launch-planning agent.
Use all four available tools in this order: extract_tasks, check_launch_readiness,
generate_owner_checklist, draft_launch_copy. Do not invent evidence. Treat missing
evidence as a risk or follow-up question. Return a concise prioritized launch plan
covering product, engineering, QA, infrastructure, security, docs, support/comms,
rollback, and monitoring/observability. Include readiness score, top risks, owner
checklist, launch copy, follow-up questions, and assumptions. Never execute a
production change; this agent plans only."""
REQUIRED_TOOLS = ("extract_tasks", "check_launch_readiness", "generate_owner_checklist", "draft_launch_copy")


def _sdk_tools():
    from agents import function_tool
    mapping = launch_desk_tool_map()
    descriptions = {
        "extract_tasks": "Extract actionable launch tasks from the request.",
        "check_launch_readiness": "Score the fixed nine-area launch readiness rubric.",
        "generate_owner_checklist": "Generate owner actions for missing readiness evidence.",
        "draft_launch_copy": "Draft concise launch communication copy.",
    }
    return [function_tool(mapping[name], name_override=name, description_override=descriptions[name]) for name in REQUIRED_TOOLS]


def _event_payload(event: Any) -> dict[str, Any] | None:
    event_type = getattr(event, "type", "")
    if event_type == "raw_response_event":
        data = getattr(event, "data", None)
        delta = getattr(data, "delta", None)
        if isinstance(delta, str) and delta:
            return {"type": "model_text_delta", "delta": delta}
    if event_type == "run_item_stream_event":
        item = getattr(event, "item", None)
        item_type = getattr(item, "type", "")
        if item_type == "tool_call_item":
            raw = getattr(item, "raw_item", None)
            name = getattr(raw, "name", None) or getattr(item, "name", None) or "unknown"
            return {"type": "tool_event", "phase": "called", "tool": str(name)}
        if item_type == "tool_call_output_item":
            raw = getattr(item, "raw_item", None)
            name = getattr(raw, "name", None) or getattr(item, "name", None) or "unknown"
            return {"type": "tool_event", "phase": "output", "tool": str(name)}
    return None


def stream_launch_desk(*, text: str, api_key: str, base_url: str, model: str, emit: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    """Run Launch Desk with the persisted provider credential and emit live events."""
    plan = build_deterministic_plan(text)
    emit({"type": "plan_ready", "plan": plan.to_dict()})

    async def run() -> str:
        from agents import Agent, OpenAIProvider, RunConfig, Runner, set_tracing_disabled
        set_tracing_disabled(disabled=True)
        provider = OpenAIProvider(api_key=api_key, base_url=base_url, use_responses=True)
        agent = Agent(name="Launch Desk", instructions=INSTRUCTIONS, tools=_sdk_tools(), model=model)
        result = Runner.run_streamed(agent, text, run_config=RunConfig(model_provider=provider, model=model), max_turns=8)
        called: set[str] = set()
        async for event in result.stream_events():
            payload = _event_payload(event)
            if payload is not None:
                if payload.get("type") == "tool_event" and payload.get("phase") == "called":
                    called.add(str(payload.get("tool")))
                emit(payload)
        if result.run_loop_exception is not None:
            raise result.run_loop_exception
        missing = [name for name in REQUIRED_TOOLS if name not in called]
        if missing:
            raise RuntimeError(f"launch_desk_required_tools_not_called: {','.join(missing)}")
        return str(result.final_output or "")

    model_text = asyncio.run(run())
    final = {"type": "final", "model_text": model_text, "plan": plan.to_dict()}
    emit(final)
    return final


def launch_desk_smoke_payload(text: str) -> dict[str, Any]:
    """Return the deterministic contract used by offline CI smoke tests."""
    plan = build_deterministic_plan(text)
    return {"status": "ok", "plan": json.loads(json.dumps(plan.to_dict(), ensure_ascii=False))}
