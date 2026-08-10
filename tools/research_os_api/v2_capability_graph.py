#!/usr/bin/env python3
"""Dynamic capability graph for Research OS AI Brain.

The graph is a read-only projection over canonical Agent, Skill and Tool
registries. It is never persisted as a second source of truth. The Brain uses it
to understand which capability is routable, which Skill contracts exist, which
Tool requirements are satisfiable, and which permissions/approvals are needed.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from agent_platform import AgentRegistry
from v2_skill_registry import SkillRegistry
from v2_tool_registry import ToolRegistry


CAPABILITY_GRAPH_CONTRACT = "brain-capability-graph-phase-10"


class CapabilityGraph:
    def __init__(
        self,
        *,
        agents: AgentRegistry,
        skills: SkillRegistry,
        tools: ToolRegistry,
    ) -> None:
        self.agents = agents
        self.skills = skills
        self.tools = tools

    def resolve(self, capabilities: Iterable[str]) -> dict[str, Any]:
        required = tuple(
            dict.fromkeys(str(value).strip() for value in capabilities if str(value).strip())
        )
        results: list[dict[str, Any]] = []
        for capability in required:
            agents = self.agents.discover(capability=capability, ready_only=True)
            skills = self.skills.discover(capability=capability, enabled_only=True)
            skill_routes: list[dict[str, Any]] = []
            for skill in skills:
                skill_id = str(skill["skill_id"])
                definition = self.skills.get(skill_id)
                named_tools = list(definition.required_tools)
                named_ready = [
                    tool_id
                    for tool_id in named_tools
                    if self._tool_ready(tool_id)
                ]
                tool_match = self.tools.match_capabilities(
                    definition.required_tool_capabilities,
                    ready_only=True,
                )
                if named_tools and definition.required_tool_capabilities:
                    candidates = sorted(set(named_ready) & set(tool_match["candidates"]))
                elif named_tools:
                    candidates = sorted(named_ready)
                elif definition.required_tool_capabilities:
                    candidates = list(tool_match["candidates"])
                else:
                    candidates = []
                executable = bool(candidates)
                skill_routes.append(
                    {
                        "skill_id": skill_id,
                        "ready": bool(skill["ready"]),
                        "permissions": list(definition.permissions),
                        "required_skills": list(definition.required_skills),
                        "required_tools": named_tools,
                        "required_tool_capabilities": list(
                            definition.required_tool_capabilities
                        ),
                        "tool_candidates": candidates,
                        "executable": executable,
                        "reasoning_only": not named_tools
                        and not definition.required_tool_capabilities,
                        "blocked_reasons": self._skill_blockers(
                            skill,
                            named_tools=named_tools,
                            named_ready=named_ready,
                            tool_match=tool_match,
                        ),
                    }
                )

            results.append(
                {
                    "capability": capability,
                    "known": bool(agents or skills or self.tools.discover(
                        capability=capability,
                        ready_only=False,
                    )),
                    "routable": bool(agents),
                    "agent_ids": [str(item["agent_id"]) for item in agents],
                    "skill_routes": skill_routes,
                    "skill_supported": bool(skills),
                    "executable_skill_ids": [
                        item["skill_id"] for item in skill_routes if item["executable"]
                    ],
                    "direct_tool_ids": [
                        str(item["tool_id"])
                        for item in self.tools.discover(
                            capability=capability,
                            ready_only=True,
                        )
                    ],
                }
            )

        return {
            "contract": CAPABILITY_GRAPH_CONTRACT,
            "required_capabilities": list(required),
            "capabilities": results,
            "all_known": bool(results) and all(item["known"] for item in results),
            "all_routable": bool(results) and all(item["routable"] for item in results),
            "all_skill_supported": bool(results)
            and all(item["skill_supported"] for item in results),
            "source_of_truth": {
                "agents": "AgentRegistry",
                "skills": "SkillRegistry",
                "tools": "ToolRegistry",
            },
            "persisted": False,
        }

    def snapshot(self) -> dict[str, Any]:
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, str]] = []
        seen_capabilities: set[str] = set()
        seen_permissions: set[str] = set()
        seen_tool_capabilities: set[str] = set()

        for agent in self.agents.list():
            agent_id = str(agent["agent_id"])
            nodes.append(
                {
                    "id": f"agent:{agent_id}",
                    "kind": "agent",
                    "ready": bool(agent["health"]["ready"]),
                }
            )
            for capability in agent.get("capabilities", ()):
                cap = str(capability)
                seen_capabilities.add(cap)
                edges.append(
                    {
                        "from": f"agent:{agent_id}",
                        "to": f"capability:{cap}",
                        "relation": "provides",
                    }
                )
            for permission in agent.get("permissions", ()):
                perm = str(permission)
                seen_permissions.add(perm)
                edges.append(
                    {
                        "from": f"agent:{agent_id}",
                        "to": f"permission:{perm}",
                        "relation": "declares",
                    }
                )

        for skill in self.skills.list():
            skill_id = str(skill["skill_id"])
            nodes.append(
                {
                    "id": f"skill:{skill_id}",
                    "kind": "skill",
                    "ready": bool(skill["ready"]),
                    "version": str(skill["version"]),
                }
            )
            for capability in skill.get("capabilities", ()):
                cap = str(capability)
                seen_capabilities.add(cap)
                edges.append(
                    {
                        "from": f"skill:{skill_id}",
                        "to": f"capability:{cap}",
                        "relation": "provides",
                    }
                )
            for dependency in skill.get("required_skills", ()):
                edges.append(
                    {
                        "from": f"skill:{skill_id}",
                        "to": f"skill:{dependency}",
                        "relation": "depends_on",
                    }
                )
            for tool_id in skill.get("required_tools", ()):
                edges.append(
                    {
                        "from": f"skill:{skill_id}",
                        "to": f"tool:{tool_id}",
                        "relation": "requires_tool",
                    }
                )
            for capability in skill.get("required_tool_capabilities", ()):
                cap = str(capability)
                seen_tool_capabilities.add(cap)
                edges.append(
                    {
                        "from": f"skill:{skill_id}",
                        "to": f"tool_capability:{cap}",
                        "relation": "requires_tool_capability",
                    }
                )
            for permission in skill.get("permissions", ()):
                perm = str(permission)
                seen_permissions.add(perm)
                edges.append(
                    {
                        "from": f"skill:{skill_id}",
                        "to": f"permission:{perm}",
                        "relation": "requires",
                    }
                )

        for tool in self.tools.list():
            tool_id = str(tool["tool_id"])
            nodes.append(
                {
                    "id": f"tool:{tool_id}",
                    "kind": "tool",
                    "ready": bool(tool["ready"]),
                    "mutating": bool(tool["mutating"]),
                    "network": bool(tool["network"]),
                }
            )
            for capability in tool.get("capabilities", ()):
                cap = str(capability)
                seen_tool_capabilities.add(cap)
                edges.append(
                    {
                        "from": f"tool:{tool_id}",
                        "to": f"tool_capability:{cap}",
                        "relation": "provides",
                    }
                )
            for permission in tool.get("permissions", ()):
                perm = str(permission)
                seen_permissions.add(perm)
                edges.append(
                    {
                        "from": f"tool:{tool_id}",
                        "to": f"permission:{perm}",
                        "relation": "requires",
                    }
                )

        nodes.extend(
            {"id": f"capability:{value}", "kind": "capability"}
            for value in sorted(seen_capabilities)
        )
        nodes.extend(
            {"id": f"tool_capability:{value}", "kind": "tool_capability"}
            for value in sorted(seen_tool_capabilities)
        )
        nodes.extend(
            {"id": f"permission:{value}", "kind": "permission"}
            for value in sorted(seen_permissions)
        )
        return {
            "contract": CAPABILITY_GRAPH_CONTRACT,
            "nodes": nodes,
            "edges": edges,
            "counts": {
                "nodes": len(nodes),
                "edges": len(edges),
                "capabilities": len(seen_capabilities),
                "tool_capabilities": len(seen_tool_capabilities),
                "permissions": len(seen_permissions),
            },
            "persisted": False,
            "duplicate_registry": False,
        }

    def _tool_ready(self, tool_id: str) -> bool:
        try:
            return bool(self.tools.describe(tool_id)["ready"])
        except ValueError:
            return False

    @staticmethod
    def _skill_blockers(
        skill: Mapping[str, Any],
        *,
        named_tools: list[str],
        named_ready: list[str],
        tool_match: Mapping[str, Any],
    ) -> list[str]:
        blocked: list[str] = []
        blocked.extend(
            f"missing skill dependency: {item}"
            for item in skill.get("missing_dependencies", ())
        )
        blocked.extend(
            f"disabled skill dependency: {item}"
            for item in skill.get("disabled_dependencies", ())
        )
        blocked.extend(
            f"required tool unavailable: {item}"
            for item in named_tools
            if item not in named_ready
        )
        blocked.extend(
            f"required tool capability unavailable: {item}"
            for item in tool_match.get("missing_capabilities", ())
        )
        if not named_tools and not skill.get("required_tool_capabilities"):
            blocked.append("reasoning-only skill has no direct tool execution contract")
        return list(dict.fromkeys(blocked))
