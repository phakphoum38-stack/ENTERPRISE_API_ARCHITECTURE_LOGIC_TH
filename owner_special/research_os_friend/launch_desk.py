from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Callable

READINESS_AREAS = (
    "product", "engineering", "QA", "infrastructure", "security", "docs",
    "support/comms", "rollback", "monitoring/observability",
)


@dataclass(frozen=True)
class LaunchTask:
    title: str
    area: str
    priority: str
    owner: str
    evidence: str = ""


@dataclass(frozen=True)
class ReadinessItem:
    area: str
    score: int
    status: str
    rationale: str
    next_action: str


@dataclass(frozen=True)
class LaunchDeskResult:
    tasks: tuple[LaunchTask, ...]
    readiness: tuple[ReadinessItem, ...]
    readiness_score: int
    risks: tuple[str, ...]
    owner_checklist: tuple[str, ...]
    launch_copy: str
    follow_up_questions: tuple[str, ...]
    assumptions: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_tasks(text: str) -> list[dict[str, str]]:
    lines = [_clean(line.lstrip("-•*0123456789. ")) for line in text.splitlines()]
    lines = [line for line in lines if line]
    if not lines and _clean(text):
        lines = [_clean(text)]
    tasks: list[dict[str, str]] = []
    for line in lines:
        lowered = line.lower()
        area = next((a for a in READINESS_AREAS if a.lower() in lowered), "engineering")
        priority = "P0" if any(x in lowered for x in ("blocker", "critical", "must")) else "P1"
        tasks.append({"title": line, "area": area, "priority": priority, "owner": "owner", "evidence": ""})
    return tasks


def check_launch_readiness(text: str, tasks: list[dict[str, str]]) -> dict[str, Any]:
    lowered = text.lower()
    items: list[dict[str, Any]] = []
    for area in READINESS_AREAS:
        key = area.lower()
        present = key in lowered or any(t.get("area", "").lower() == key for t in tasks)
        score = 100 if present else 35
        items.append({
            "area": area,
            "score": score,
            "status": "ready" if present else "needs-attention",
            "rationale": "Evidence or an explicit task is present." if present else "No explicit evidence was provided.",
            "next_action": "Confirm owner and acceptance evidence." if present else f"Add a concrete {area} gate before launch.",
        })
    return {"items": items, "score": round(sum(item["score"] for item in items) / len(items))}


def generate_owner_checklist(readiness: dict[str, Any]) -> list[str]:
    pending = [
        f"Confirm {item['area']} owner and acceptance evidence: {item['next_action']}"
        for item in readiness["items"] if item["status"] != "ready"
    ]
    return pending or ["Confirm final go/no-go approval and capture evidence for all nine readiness areas."]


def draft_launch_copy(text: str, readiness_score: int) -> str:
    subject = _clean(text)[:120] or "Research OS launch"
    return (f"Launch update: {subject}. Readiness is currently {readiness_score}/100 based on the "
            "provided evidence. We are completing the remaining launch gates, validating rollback "
            "and monitoring, and will announce go-live after final owner approval.")


class LaunchDeskTools:
    """Deterministic functions used by the Launch Desk agent."""

    @staticmethod
    def extract_tasks(text: str) -> str:
        return __import__("json").dumps(extract_tasks(text), ensure_ascii=False)

    @staticmethod
    def check_launch_readiness(text: str) -> str:
        import json
        tasks = extract_tasks(text)
        return json.dumps(check_launch_readiness(text, tasks), ensure_ascii=False)

    @staticmethod
    def generate_owner_checklist(text: str) -> str:
        import json
        readiness = check_launch_readiness(text, extract_tasks(text))
        return json.dumps(generate_owner_checklist(readiness), ensure_ascii=False)

    @staticmethod
    def draft_launch_copy(text: str) -> str:
        readiness = check_launch_readiness(text, extract_tasks(text))
        return draft_launch_copy(text, readiness["score"])


def build_deterministic_plan(text: str) -> LaunchDeskResult:
    tasks_raw = extract_tasks(text)
    readiness_raw = check_launch_readiness(text, tasks_raw)
    readiness = tuple(ReadinessItem(**item) for item in readiness_raw["items"])
    tasks = tuple(LaunchTask(**task) for task in tasks_raw)
    risks = tuple(f"{item.area}: {item.next_action}" for item in readiness if item.status != "ready")
    checklist = tuple(generate_owner_checklist(readiness_raw))
    questions = tuple(
        f"Who owns the {item.area} gate and what evidence proves it is complete?"
        for item in readiness if item.status != "ready"
    )
    return LaunchDeskResult(
        tasks=tasks,
        readiness=readiness,
        readiness_score=int(readiness_raw["score"]),
        risks=risks,
        owner_checklist=checklist,
        launch_copy=draft_launch_copy(text, int(readiness_raw["score"])),
        follow_up_questions=questions[:8],
        assumptions=(
            "Readiness is scored only from evidence supplied in the request.",
            "Missing evidence is treated as needs-attention, not as a confirmed failure.",
            "No production change is executed by Launch Desk planning.",
        ),
    )


ToolFunction = Callable[[str], str]


def launch_desk_tool_map() -> dict[str, ToolFunction]:
    return {
        "extract_tasks": LaunchDeskTools.extract_tasks,
        "check_launch_readiness": LaunchDeskTools.check_launch_readiness,
        "generate_owner_checklist": LaunchDeskTools.generate_owner_checklist,
        "draft_launch_copy": LaunchDeskTools.draft_launch_copy,
    }
