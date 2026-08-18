from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from .research_tools import ResearchToolRegistry, ToolRequest, ToolResult


@dataclass(frozen=True)
class ToolEvidence:
    evidence_id: str
    task_id: str | None
    tool_name: str
    capability: str
    source_uri: str | None
    output: Any
    metadata: Mapping[str, str]


class EvidenceSink(Protocol):
    def add(self, evidence: ToolEvidence) -> None: ...


class InMemoryEvidenceSink:
    def __init__(self) -> None:
        self.items: list[ToolEvidence] = []

    def add(self, evidence: ToolEvidence) -> None:
        self.items.append(evidence)


class ToolEvidenceRecorder:
    """Executes research tools and converts successful results into provenance records."""

    def __init__(self, registry: ResearchToolRegistry, sink: EvidenceSink) -> None:
        self.registry = registry
        self.sink = sink

    def execute(self, request: ToolRequest) -> ToolResult:
        result = self.registry.execute(request)
        if result.success:
            payload = json.dumps(result.output, sort_keys=True, default=str)
            fingerprint = hashlib.sha256(
                f"{request.task_id}|{request.capability}|{result.tool_name}|{result.source_uri}|{payload}".encode()
            ).hexdigest()
            self.sink.add(
                ToolEvidence(
                    evidence_id=f"tool-{fingerprint[:24]}",
                    task_id=request.task_id,
                    tool_name=result.tool_name,
                    capability=request.capability,
                    source_uri=result.source_uri,
                    output=result.output,
                    metadata=result.metadata,
                )
            )
        return result
