#!/usr/bin/env python3
"""Governed tool intelligence for Research OS.

This layer teaches the Unified Master how to understand existing tools, identify
capability gaps, research external tools through the configured web-search
provider, evaluate evidence, design an adapter plan, and learn from structured
tool outcomes. It never downloads, installs, registers, or executes a discovered
external tool automatically.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urlsplit

from providers import AIProvider, ProviderError, build_search_provider
from v2_learning_engine import LearningEngine
from v2_secret_redactor import sanitize_external
from v2_tool_registry import ToolRegistry


TOOL_INTELLIGENCE_CONTRACT = "brain-tool-intelligence-v1"
_MAX_OBJECTIVE_CHARS = 8_000
_MAX_CAPABILITIES = 64
_MAX_CANDIDATES = 12

# Research OS may evaluate many software categories, but the discovery layer
# intentionally refuses categories that should not be surfaced through an
# autonomous tool-finding workflow.
_BLOCKED_DISCOVERY_TERMS = (
    "firearm",
    "gun",
    "weapon",
    "explosive",
    "bomb",
    "casino",
    "gambling",
    "betting",
    "sportsbook",
    "porn",
    "pornography",
    "vape",
    "nicotine",
    "cannabis",
    "recreational drug",
    "self-harm",
    "self harm",
)

_DISCOVERY_KEYWORDS = (
    "ค้นหาเครื่องมือ",
    "หาเครื่องมือ",
    "ค้นซอฟต์แวร์",
    "หาซอฟต์แวร์",
    "ค้น plugin",
    "ค้น plugin",
    "search tools",
    "find tools",
    "discover tools",
    "find software",
    "search software",
    "find plugin",
    "find mcp",
)


@dataclass(frozen=True)
class ToolDiscoveryPolicy:
    web_research: bool = True
    official_sources_preferred: bool = True
    provenance_required: bool = True
    automatic_download: bool = False
    automatic_install: bool = False
    automatic_registration: bool = False
    automatic_execution: bool = False
    automatic_permission_grant: bool = False
    adapter_plan_only: bool = True
    review_required: bool = True


@dataclass(frozen=True)
class ToolCandidate:
    name: str
    url: str
    publisher: str
    tool_type: str
    capabilities: tuple[str, ...]
    integration_modes: tuple[str, ...]
    platforms: tuple[str, ...]
    license: str
    requires_credentials: bool
    network_required: bool
    evidence_urls: tuple[str, ...]
    risk_level: str
    trust_score: int
    recommendation: str


def _bounded_text(value: Any, *, limit: int = 512) -> str:
    safe = sanitize_external(str(value or "").strip())
    if not isinstance(safe, str):
        return ""
    return safe if len(safe) <= limit else safe[: limit - 3] + "..."


def _strings(values: Iterable[Any], *, limit: int = _MAX_CAPABILITIES) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        text = _bounded_text(value, limit=128)
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return tuple(result)


def _https_url(value: Any) -> str:
    text = _bounded_text(value, limit=2_048)
    if not text:
        return ""
    parsed = urlsplit(text)
    if parsed.scheme.casefold() != "https" or not parsed.netloc:
        return ""
    return text


def _extract_json(text: str) -> Any:
    stripped = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", stripped, flags=re.I | re.S)
    if fenced:
        stripped = fenced.group(1).strip()
    for candidate in (stripped,):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    starts = [index for index in (stripped.find("{"), stripped.find("[")) if index >= 0]
    if not starts:
        return None
    start = min(starts)
    for end in range(len(stripped), start, -1):
        if stripped[end - 1] not in "}]":
            continue
        try:
            return json.loads(stripped[start:end])
        except json.JSONDecodeError:
            continue
    return None


class ToolIntelligence:
    """Read-mostly intelligence over the canonical ToolRegistry and LearningEngine."""

    def __init__(
        self,
        registry: ToolRegistry,
        learning: LearningEngine,
        *,
        search_provider_factory: Callable[[str | None], AIProvider] = build_search_provider,
    ) -> None:
        self.registry = registry
        self.learning = learning
        self.search_provider_factory = search_provider_factory
        self.policy = ToolDiscoveryPolicy()

    def dashboard(self) -> dict[str, Any]:
        return {
            "contract": TOOL_INTELLIGENCE_CONTRACT,
            "current_tools": self.registry.dashboard(),
            "policy": asdict(self.policy),
            "discovery_sources": [
                {
                    "source": "Official MCP Registry",
                    "kind": "mcp_registry",
                    "use": "discover MCP servers and standardized server metadata",
                },
                {
                    "source": "GitHub Marketplace",
                    "kind": "developer_marketplace",
                    "use": "discover GitHub Apps and Actions with publisher/repository evidence",
                },
                {
                    "source": "PyPI",
                    "kind": "python_registry",
                    "use": "discover Python packages and inspect project/release metadata",
                },
                {
                    "source": "npm registry",
                    "kind": "javascript_registry",
                    "use": "discover JavaScript/Node packages and package metadata",
                },
                {
                    "source": "official vendor/project websites",
                    "kind": "general_web",
                    "use": "fill capability gaps not covered by structured registries",
                },
            ],
            "selection_strategy": "capability_coverage_then_readiness_then_minimum_risk",
            "external_tool_execution": False,
            "self_installation": False,
        }

    @staticmethod
    def should_discover(objective: str) -> bool:
        normalized = " ".join(str(objective or "").casefold().split())
        return any(keyword in normalized for keyword in _DISCOVERY_KEYWORDS)

    @staticmethod
    def _validate_objective(objective: str) -> str:
        text = _bounded_text(objective, limit=_MAX_OBJECTIVE_CHARS)
        if not text:
            raise ValueError("objective is required")
        lowered = text.casefold()
        if any(term in lowered for term in _BLOCKED_DISCOVERY_TERMS):
            raise ValueError("tool discovery is not available for this restricted category")
        return text

    def infer_capabilities(self, objective: str) -> tuple[str, ...]:
        text = self._validate_objective(objective).casefold()
        routes = {
            "web_search": ("เว็บ", "web", "search", "ค้นหา", "research"),
            "source_control": ("git", "github", "repository", "source control", "repo"),
            "workspace_files": ("file", "folder", "document", "ไฟล์", "เอกสาร"),
            "code_execution": ("code", "python", "script", "โค้ด", "รัน"),
            "package_management": ("package", "dependency", "pip", "npm", "แพ็กเกจ"),
            "browser_automation": ("browser", "web automation", "เบราว์เซอร์"),
            "data_analysis": ("data", "analytics", "csv", "excel", "ข้อมูล", "วิเคราะห์"),
            "database": ("database", "sql", "ฐานข้อมูล"),
            "calendar": ("calendar", "schedule", "ปฏิทิน", "นัดหมาย"),
            "email": ("email", "gmail", "อีเมล"),
            "api_integration": ("api", "sdk", "webhook", "integration", "เชื่อมต่อ"),
            "testing": ("test", "qa", "verification", "ทดสอบ"),
        }
        selected = [
            capability
            for capability, keywords in routes.items()
            if any(keyword in text for keyword in keywords)
        ]
        return tuple(selected)

    def rank_existing(self, capabilities: Iterable[str]) -> dict[str, Any]:
        required = _strings(capabilities)
        if not required:
            return {
                "contract": TOOL_INTELLIGENCE_CONTRACT,
                "required_capabilities": [],
                "ranked": [],
                "selected_tool_id": None,
                "missing_capabilities": [],
            }

        ranked: list[dict[str, Any]] = []
        covered: set[str] = set()
        for item in self.registry.list():
            tool_caps = {str(value).casefold() for value in item.get("capabilities", ())}
            matched = [cap for cap in required if cap.casefold() in tool_caps]
            if not matched:
                continue
            covered.update(matched)
            coverage = len(matched) / len(required)
            risk_penalty = 0
            risk_penalty += 28 if item.get("destructive") else 0
            risk_penalty += 14 if item.get("mutating") else 0
            risk_penalty += 8 if item.get("secret_access") else 0
            risk_penalty += 5 if item.get("network") else 0
            risk_penalty += 4 if not item.get("supports_dry_run", False) else 0
            score = round((coverage * 100) + (25 if item.get("ready") else 0) - risk_penalty, 2)
            ranked.append(
                {
                    "tool_id": item["tool_id"],
                    "name": item["name"],
                    "matched_capabilities": matched,
                    "coverage": round(coverage, 3),
                    "ready": bool(item.get("ready")),
                    "score": score,
                    "risk": {
                        "mutating": bool(item.get("mutating")),
                        "destructive": bool(item.get("destructive")),
                        "network": bool(item.get("network")),
                        "secret_access": bool(item.get("secret_access")),
                    },
                }
            )
        ranked.sort(key=lambda item: (-float(item["score"]), str(item["tool_id"])))
        missing = [cap for cap in required if cap not in covered]
        selected = next(
            (
                item["tool_id"]
                for item in ranked
                if item["ready"] and float(item["coverage"]) == 1.0
            ),
            ranked[0]["tool_id"] if ranked else None,
        )
        return {
            "contract": TOOL_INTELLIGENCE_CONTRACT,
            "required_capabilities": list(required),
            "ranked": ranked,
            "selected_tool_id": selected,
            "missing_capabilities": missing,
            "selection_executes_tool": False,
        }

    def plan_for_objective(
        self,
        objective: str,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        text = self._validate_objective(objective)
        raw_context = dict(context or {})
        requested = raw_context.get("required_tool_capabilities")
        if isinstance(requested, (list, tuple)):
            capabilities = _strings(requested)
        else:
            capabilities = self.infer_capabilities(text)
        existing = self.rank_existing(capabilities)
        needs_external = bool(existing["missing_capabilities"]) or self.should_discover(text)
        return {
            "contract": TOOL_INTELLIGENCE_CONTRACT,
            "objective": text,
            "required_capabilities": list(capabilities),
            "existing": existing,
            "needs_external_discovery": needs_external,
            "external_discovery_trigger": (
                "explicit_request" if self.should_discover(text) else "capability_gap"
            ),
            "discovery_plan": self.discovery_plan(
                text,
                existing["missing_capabilities"] or capabilities,
            )
            if needs_external
            else None,
            "execution_performed": False,
        }

    def discovery_plan(
        self,
        objective: str,
        capabilities: Iterable[str],
    ) -> dict[str, Any]:
        text = self._validate_objective(objective)
        required = _strings(capabilities)
        return {
            "contract": TOOL_INTELLIGENCE_CONTRACT,
            "objective": text,
            "capabilities": list(required),
            "search_order": [
                "Official MCP Registry",
                "GitHub Marketplace",
                "PyPI",
                "npm registry",
                "official vendor/project websites",
            ],
            "evidence_required": [
                "official or canonical project URL",
                "publisher/owner",
                "current version or maintenance evidence",
                "license when applicable",
                "supported platforms",
                "integration/API/MCP/CLI mode",
                "authentication and permission requirements",
                "security or provenance evidence",
            ],
            "evaluation": [
                "capability fit",
                "source provenance",
                "maintenance evidence",
                "license clarity",
                "permission scope",
                "credential exposure risk",
                "network/runtime risk",
                "adapter complexity",
                "testability and rollback",
            ],
            "automatic_install": False,
            "review_required": True,
        }

    def discover(
        self,
        objective: str,
        *,
        capabilities: Iterable[str] = (),
        provider_name: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        text = self._validate_objective(objective)
        required = _strings(capabilities) or self.infer_capabilities(text)
        plan = self.discovery_plan(text, required)
        provider: AIProvider
        try:
            provider = self.search_provider_factory(provider_name)
        except ProviderError as exc:
            return {
                "contract": TOOL_INTELLIGENCE_CONTRACT,
                "objective": text,
                "plan": plan,
                "provider_ready": False,
                "provider_error": _bounded_text(exc, limit=256),
                "candidates": [],
                "sources": [],
                "automatic_install": False,
            }

        query = (
            "Research software tools for this objective: " + text + "\n"
            "Required capabilities: " + ", ".join(required or ("unspecified",)) + "\n"
            "Search reputable sources globally. Prefer official MCP Registry metadata, "
            "GitHub Marketplace or canonical repositories, PyPI, npm registry, and official "
            "vendor/project documentation. Do not suggest restricted or age-restricted "
            "products. Do not provide download/install commands. Return up to 8 candidates "
            "as strict JSON with key 'candidates'. Each candidate must include name, url, "
            "publisher, tool_type, capabilities, integration_modes, platforms, license, "
            "requires_credentials, network_required, evidence_urls, risk_level, and recommendation."
        )
        system = (
            "You are the Research OS Tool Intelligence researcher. Prefer primary/official "
            "sources, separate evidence from inference, do not expose credentials, and never "
            "install or execute discovered tools. Return candidate metadata only."
        )
        try:
            result = provider.search(query, system=system, model=model)
        except ProviderError as exc:
            return {
                "contract": TOOL_INTELLIGENCE_CONTRACT,
                "objective": text,
                "plan": plan,
                "provider_ready": True,
                "provider": provider.name,
                "provider_error": _bounded_text(exc, limit=256),
                "candidates": [],
                "sources": [],
                "automatic_install": False,
            }

        candidates = self._candidates_from_text(result.text, result.sources)
        return {
            "contract": TOOL_INTELLIGENCE_CONTRACT,
            "objective": text,
            "plan": plan,
            "provider_ready": True,
            "provider": result.provider,
            "model": result.model,
            "candidates": [asdict(item) for item in candidates],
            "sources": list(result.sources),
            "raw_recommendation": _bounded_text(result.text, limit=4_000),
            "automatic_download": False,
            "automatic_install": False,
            "automatic_registration": False,
            "automatic_execution": False,
            "review_required": True,
        }

    def _candidates_from_text(
        self,
        text: str,
        provider_sources: Iterable[Mapping[str, Any]],
    ) -> list[ToolCandidate]:
        payload = _extract_json(text)
        if isinstance(payload, Mapping):
            raw_candidates = payload.get("candidates")
        elif isinstance(payload, list):
            raw_candidates = payload
        else:
            raw_candidates = None
        if not isinstance(raw_candidates, list):
            return []

        provider_urls = tuple(
            url
            for source in provider_sources
            if isinstance(source, Mapping)
            for url in (_https_url(source.get("url")),)
            if url
        )
        result: list[ToolCandidate] = []
        for raw in raw_candidates[:_MAX_CANDIDATES]:
            if not isinstance(raw, Mapping):
                continue
            url = _https_url(raw.get("url"))
            if not url:
                continue
            evidence_urls = _strings(
                [
                    *(
                        raw.get("evidence_urls")
                        if isinstance(raw.get("evidence_urls"), list)
                        else []
                    ),
                    *provider_urls,
                ],
                limit=16,
            )
            evidence_urls = tuple(filter(None, (_https_url(value) for value in evidence_urls)))
            license_name = _bounded_text(raw.get("license"), limit=96) or "unknown"
            risk_level = _bounded_text(raw.get("risk_level"), limit=32).casefold()
            if risk_level not in {"low", "medium", "high"}:
                risk_level = "medium"
            trust = 35
            trust += 15 if url.startswith("https://") else 0
            trust += min(25, len(evidence_urls) * 5)
            trust += 10 if license_name.casefold() not in {"", "unknown", "unspecified"} else 0
            trust += 5 if _bounded_text(raw.get("publisher"), limit=128) else 0
            trust -= 15 if risk_level == "high" else 5 if risk_level == "medium" else 0
            trust = max(0, min(100, trust))
            result.append(
                ToolCandidate(
                    name=_bounded_text(raw.get("name"), limit=160) or urlsplit(url).netloc,
                    url=url,
                    publisher=_bounded_text(raw.get("publisher"), limit=160) or "unknown",
                    tool_type=_bounded_text(raw.get("tool_type"), limit=96) or "unknown",
                    capabilities=_strings(raw.get("capabilities") or (), limit=32),
                    integration_modes=_strings(raw.get("integration_modes") or (), limit=16),
                    platforms=_strings(raw.get("platforms") or (), limit=16),
                    license=license_name,
                    requires_credentials=bool(raw.get("requires_credentials", False)),
                    network_required=bool(raw.get("network_required", True)),
                    evidence_urls=evidence_urls,
                    risk_level=risk_level,
                    trust_score=trust,
                    recommendation=_bounded_text(raw.get("recommendation"), limit=512),
                )
            )
        result.sort(key=lambda item: (-item.trust_score, item.name.casefold()))
        return result

    def design_adapter(self, candidate: Mapping[str, Any]) -> dict[str, Any]:
        name = _bounded_text(candidate.get("name"), limit=160)
        url = _https_url(candidate.get("url"))
        if not name or not url:
            raise ValueError("candidate name and HTTPS url are required")
        capabilities = _strings(candidate.get("capabilities") or (), limit=32)
        integration_modes = _strings(candidate.get("integration_modes") or (), limit=16)
        requires_credentials = bool(candidate.get("requires_credentials", False))
        network_required = bool(candidate.get("network_required", True))
        return {
            "contract": TOOL_INTELLIGENCE_CONTRACT,
            "candidate": {
                "name": name,
                "url": url,
                "capabilities": list(capabilities),
                "integration_modes": list(integration_modes),
            },
            "adapter_plan": {
                "reuse_first": True,
                "preferred_boundary": "ToolRegistry metadata + permissioned ExecutionController adapter",
                "steps": [
                    "verify canonical publisher/source and version",
                    "review license and platform compatibility",
                    "map only required capabilities and minimum permissions",
                    "define secret references by environment-variable name only",
                    "implement read-only/dry-run path first when supported",
                    "add deterministic adapter contract and input validation",
                    "add unit tests with mock/fake service responses",
                    "add integration test behind explicit opt-in",
                    "record evidence and rollback procedure",
                    "request review before registration or execution",
                ],
                "network_required": network_required,
                "credential_boundary_required": requires_credentials,
                "automatic_code_generation": False,
                "automatic_registration": False,
                "automatic_installation": False,
                "automatic_execution": False,
                "review_required": True,
            },
        }

    def tool_playbook(self, tool_id: str) -> dict[str, Any]:
        tool = self.registry.describe(tool_id)
        patterns = self.learning.patterns()
        outcomes = patterns.get("tool_outcomes", {}).get(tool_id, {})
        verified = int(outcomes.get("verified", 0))
        adverse = sum(
            int(outcomes.get(name, 0))
            for name in ("failed", "blocked", "verification_failed")
        )
        confidence = "established" if verified >= 3 and adverse == 0 else "mixed" if verified else "unproven"
        return {
            "contract": TOOL_INTELLIGENCE_CONTRACT,
            "tool": tool,
            "observed_outcomes": outcomes,
            "usage_confidence": confidence,
            "guidance": {
                "prefer_dry_run": bool(tool.get("supports_dry_run")),
                "approval_expected": bool(tool.get("mutating") or tool.get("destructive")),
                "network_boundary": bool(tool.get("network")),
                "secret_boundary": bool(tool.get("secret_access")),
            },
            "hidden_reasoning_used": False,
        }
