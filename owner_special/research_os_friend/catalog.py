from __future__ import annotations

from .skills import Skill, SkillRegistry
from .tools import Tool, ToolRegistry
from .schedule_generation.adapter import ScheduleGenerateTool


def _tag(label: str):
    def handler(text: str) -> str:
        return f"{label}: {text.strip()}"
    return handler


def install_builtin_skills(registry: SkillRegistry) -> SkillRegistry:
    definitions = (
        ("analysis", "reasoning", "Analyze goals, constraints, and evidence."),
        ("planning", "orchestration", "Turn a goal into reviewable execution steps."),
        ("coding", "engineering", "Design, implement, test, and review software changes."),
        ("research", "knowledge", "Gather and compare source-backed information."),
        ("data", "analytics", "Inspect structured data and produce quantitative findings."),
        ("documents", "artifacts", "Create and transform durable written artifacts."),
        ("automation", "operations", "Define repeatable scheduled or triggered workflows."),
        ("memory", "context", "Use owner-scoped context without cross-profile leakage."),
        ("security", "assurance", "Apply permission, secret, and isolation boundaries."),
        ("quality", "assurance", "Validate outputs with tests and evidence."),
    )
    for name, domain, description in definitions:
        registry.register(Skill(name, domain, description, _tag(name)))
    return registry


def install_builtin_tools(registry: ToolRegistry) -> ToolRegistry:
    registry.register(Tool("echo", "Deterministic local diagnostic tool.", _tag("tool:echo")))
    registry.register(Tool("summarize", "Local summary adapter for smoke/testing.", _tag("tool:summarize")))

    schedule_generate = ScheduleGenerateTool()
    registry.register(
        Tool(
            schedule_generate.name,
            schedule_generate.description,
            schedule_generate,
        )
    )

    return registry
