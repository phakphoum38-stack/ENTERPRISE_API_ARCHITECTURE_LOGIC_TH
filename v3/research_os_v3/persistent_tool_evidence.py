from __future__ import annotations

import json

from .evidence import Evidence
from .persistent_evidence import SQLiteEvidenceStore
from .tool_evidence import ToolEvidence


class PersistentToolEvidenceSink:
    """Maps tool provenance records into the canonical durable Evidence store."""

    def __init__(self, store: SQLiteEvidenceStore, *, confidence: float = 0.8) -> None:
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        self.store = store
        self.confidence = confidence

    def add(self, evidence: ToolEvidence) -> None:
        source_uri = evidence.source_uri or f"tool://{evidence.tool_name}/{evidence.capability}"
        excerpt = json.dumps(evidence.output, sort_keys=True, ensure_ascii=False, default=str)
        claim = f"Tool {evidence.tool_name} returned evidence for capability {evidence.capability}."
        metadata = {str(k): str(v) for k, v in evidence.metadata.items()}
        metadata["tool_name"] = evidence.tool_name
        metadata["capability"] = evidence.capability
        self.store.add(
            Evidence(
                id=evidence.evidence_id,
                claim=claim,
                source_uri=source_uri,
                excerpt=excerpt,
                task_id=evidence.task_id,
                confidence=self.confidence,
                metadata=metadata,
            )
        )
