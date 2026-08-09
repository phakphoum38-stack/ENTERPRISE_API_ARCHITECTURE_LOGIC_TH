#!/usr/bin/env python3
"""Research OS V2 workspace and local knowledge engine.

Extends the existing Research Curator artifact parser with workspace boundaries,
incremental local indexing, provenance, duplicate/conflict detection and
portable metadata export/import. Uses only the Python standard library.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from knowledge_ops import load_all


_SCHEMA_VERSION = 1


def _normalize(value: str) -> str:
    return re.sub(r"\W+", " ", value, flags=re.UNICODE).strip().casefold()


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass
class Provenance:
    source_type: str
    source_id: str
    source_path: str | None = None
    evidence: list[str] = field(default_factory=list)
    imported_at: float = field(default_factory=time.time)


@dataclass
class KnowledgeRecord:
    record_id: str
    workspace_id: str
    kind: str
    title: str
    content: str
    content_hash: str
    provenance: Provenance
    tags: list[str] = field(default_factory=list)
    updated_at: float = field(default_factory=time.time)


@dataclass
class Workspace:
    workspace_id: str
    name: str
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class WorkspaceKnowledgeEngine:
    """Local-first workspace index with one durable JSON source of truth."""

    def __init__(self, data_dir: str | Path) -> None:
        self.root = Path(data_dir) / "workspaces"
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "workspace-index.json"
        self._workspaces: dict[str, Workspace] = {}
        self._records: dict[str, KnowledgeRecord] = {}
        self._load()

    def create_workspace(self, name: str, *, workspace_id: str | None = None) -> dict[str, Any]:
        normalized = name.strip()
        if not normalized:
            raise ValueError("workspace name is required")
        identifier = (workspace_id or str(uuid.uuid4())).strip()
        if identifier in self._workspaces:
            raise ValueError(f"workspace already exists: {identifier}")
        workspace = Workspace(identifier, normalized)
        self._workspaces[identifier] = workspace
        self._persist()
        return asdict(workspace)

    def list_workspaces(self) -> list[dict[str, Any]]:
        return [asdict(item) for item in sorted(self._workspaces.values(), key=lambda x: x.created_at)]

    def get_workspace(self, workspace_id: str) -> dict[str, Any]:
        return asdict(self._require_workspace(workspace_id))

    def upsert_record(
        self,
        workspace_id: str,
        *,
        kind: str,
        title: str,
        content: str,
        provenance: Provenance,
        tags: Iterable[str] = (),
        record_id: str | None = None,
    ) -> dict[str, Any]:
        workspace = self._require_workspace(workspace_id)
        text = content.strip()
        if not text:
            raise ValueError("record content is required")
        identifier = record_id or f"{provenance.source_type}:{provenance.source_id}"
        now = time.time()
        record = KnowledgeRecord(
            record_id=identifier,
            workspace_id=workspace_id,
            kind=kind.strip() or "unknown",
            title=title.strip() or identifier,
            content=text,
            content_hash=_digest(text),
            provenance=provenance,
            tags=sorted({item.strip() for item in tags if item.strip()}),
            updated_at=now,
        )
        previous = self._records.get(identifier)
        changed = previous is None or previous.content_hash != record.content_hash or previous.workspace_id != workspace_id
        self._records[identifier] = record
        workspace.updated_at = now
        if changed:
            self._persist()
        return {**self._record_payload(record), "changed": changed}

    def index_research_artifacts(self, workspace_id: str, artifact_dir: str | Path) -> dict[str, Any]:
        self._require_workspace(workspace_id)
        added = updated = unchanged = 0
        for artifact in load_all(Path(artifact_dir)):
            content = artifact.path.read_text(encoding="utf-8")
            existing = self._records.get(f"research_artifact:{artifact.artifact_id}")
            result = self.upsert_record(
                workspace_id,
                kind="research_artifact",
                title=artifact.title,
                content=content,
                provenance=Provenance(
                    source_type="research_artifact",
                    source_id=artifact.artifact_id,
                    source_path=str(artifact.path),
                    evidence=list(artifact.sections.get("Evidence", [])),
                ),
                tags=(artifact.status,),
            )
            if not result["changed"]:
                unchanged += 1
            elif existing is None:
                added += 1
            else:
                updated += 1
        return {"added": added, "updated": updated, "unchanged": unchanged, "total": added + updated + unchanged}

    def search(
        self,
        workspace_id: str,
        query: str,
        *,
        kinds: Iterable[str] = (),
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        self._require_workspace(workspace_id)
        if limit < 1 or limit > 200:
            raise ValueError("limit must be between 1 and 200")
        terms = [term for term in _normalize(query).split() if term]
        allowed_kinds = {item.casefold() for item in kinds if item}
        scored: list[tuple[int, KnowledgeRecord]] = []
        for record in self._records.values():
            if record.workspace_id != workspace_id:
                continue
            if allowed_kinds and record.kind.casefold() not in allowed_kinds:
                continue
            haystack = _normalize(" ".join([record.title, record.content, " ".join(record.tags), " ".join(record.provenance.evidence)]))
            score = sum(2 if term in _normalize(record.title) else 1 for term in terms if term in haystack)
            if not terms or score > 0:
                scored.append((score, record))
        scored.sort(key=lambda item: (item[0], item[1].updated_at), reverse=True)
        return [{**self._record_payload(record), "score": score} for score, record in scored[:limit]]

    def detect_duplicates_and_conflicts(self, workspace_id: str) -> dict[str, Any]:
        self._require_workspace(workspace_id)
        records = [item for item in self._records.values() if item.workspace_id == workspace_id]
        by_hash: dict[str, list[KnowledgeRecord]] = {}
        by_source: dict[tuple[str, str], list[KnowledgeRecord]] = {}
        for record in records:
            by_hash.setdefault(record.content_hash, []).append(record)
            key = (record.provenance.source_type, record.provenance.source_id)
            by_source.setdefault(key, []).append(record)
        duplicates = [
            [item.record_id for item in group]
            for group in by_hash.values()
            if len(group) > 1
        ]
        conflicts = [
            {
                "source_type": key[0],
                "source_id": key[1],
                "record_ids": [item.record_id for item in group],
                "content_hashes": sorted({item.content_hash for item in group}),
            }
            for key, group in by_source.items()
            if len({item.content_hash for item in group}) > 1
        ]
        return {"duplicates": duplicates, "conflicts": conflicts}

    def export_workspace(self, workspace_id: str, target: str | Path) -> Path:
        workspace = self._require_workspace(workspace_id)
        records = [self._record_payload(item) for item in self._records.values() if item.workspace_id == workspace_id]
        payload = {
            "schema_version": _SCHEMA_VERSION,
            "workspace": asdict(workspace),
            "records": records,
            "exported_at": time.time(),
        }
        path = Path(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def import_workspace(self, source: str | Path, *, replace: bool = False) -> dict[str, Any]:
        payload = json.loads(Path(source).read_text(encoding="utf-8"))
        if payload.get("schema_version") != _SCHEMA_VERSION:
            raise ValueError("unsupported workspace schema")
        raw_workspace = payload.get("workspace") or {}
        workspace_id = str(raw_workspace.get("workspace_id") or "").strip()
        if not workspace_id:
            raise ValueError("workspace_id is required in import")
        if workspace_id in self._workspaces and not replace:
            raise ValueError(f"workspace already exists: {workspace_id}")
        self._workspaces[workspace_id] = Workspace(
            workspace_id=workspace_id,
            name=str(raw_workspace.get("name") or workspace_id),
            created_at=float(raw_workspace.get("created_at") or time.time()),
            updated_at=float(raw_workspace.get("updated_at") or time.time()),
        )
        imported = 0
        for raw in payload.get("records", []):
            provenance_raw = raw.get("provenance") or {}
            provenance = Provenance(
                source_type=str(provenance_raw.get("source_type") or "unknown"),
                source_id=str(provenance_raw.get("source_id") or raw.get("record_id") or "unknown"),
                source_path=provenance_raw.get("source_path"),
                evidence=list(provenance_raw.get("evidence") or []),
                imported_at=float(provenance_raw.get("imported_at") or time.time()),
            )
            self.upsert_record(
                workspace_id,
                kind=str(raw.get("kind") or "unknown"),
                title=str(raw.get("title") or raw.get("record_id") or "Imported record"),
                content=str(raw.get("content") or ""),
                provenance=provenance,
                tags=list(raw.get("tags") or []),
                record_id=str(raw.get("record_id") or "") or None,
            )
            imported += 1
        self._persist()
        return {"workspace_id": workspace_id, "records_imported": imported}

    def _require_workspace(self, workspace_id: str) -> Workspace:
        try:
            return self._workspaces[workspace_id]
        except KeyError as exc:
            raise ValueError(f"unknown workspace: {workspace_id}") from exc

    @staticmethod
    def _record_payload(record: KnowledgeRecord) -> dict[str, Any]:
        payload = asdict(record)
        payload["provenance"] = asdict(record.provenance)
        return payload

    def _load(self) -> None:
        if not self.path.exists():
            return
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != _SCHEMA_VERSION:
            raise RuntimeError("unsupported workspace index schema")
        for raw in payload.get("workspaces", []):
            item = Workspace(**raw)
            self._workspaces[item.workspace_id] = item
        for raw in payload.get("records", []):
            provenance = Provenance(**raw.pop("provenance"))
            item = KnowledgeRecord(provenance=provenance, **raw)
            self._records[item.record_id] = item

    def _persist(self) -> None:
        payload = {
            "schema_version": _SCHEMA_VERSION,
            "workspaces": [asdict(item) for item in self._workspaces.values()],
            "records": [self._record_payload(item) for item in self._records.values()],
        }
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(self.path)
