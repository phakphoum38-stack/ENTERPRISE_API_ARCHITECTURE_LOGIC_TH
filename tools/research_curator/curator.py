#!/usr/bin/env python3
"""Research Curator CLI v0.2.

Transforms a conversation export or plain text into a versioned research artifact.
Adds deterministic knowledge filtering, knowledge-diff detection, relationship
validation, and evidence-aware truth-status transitions without external packages.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


STATUS_FLOW = (
    "new",
    "hypothesis",
    "experimenting",
    "observed",
    "repeated",
    "validated",
    "standardized",
    "deprecated",
)
STATUS_VALUES = set(STATUS_FLOW)
RELATION_VALUES = {
    "relates_to",
    "supports",
    "contradicts",
    "extends",
    "depends_on",
    "derived_from",
    "supersedes",
    "verified_by",
    "implements",
}
LOW_VALUE_PATTERNS = (
    r"^(ครับ|ค่ะ|คะ|โอเค|ok|yes|ใช่|เยี่ยม|ดีมาก|จัดไป|เริ่ม|ต่อเลย)[.! ]*$",
    r"^(ขอบคุณ|รับทราบ|ได้เลย)[ครับค่ะคะผม !.]*$",
)
KNOWLEDGE_SIGNALS = (
    "ควร", "ไม่ควร", "ต้อง", "หลักการ", "แนวคิด", "สมมติฐาน", "ค้นพบ",
    "ตัดสินใจ", "สรุป", "โมเดล", "โครงสร้าง", "เหตุผล", "ปัญหา", "วิธี",
    "architecture", "principle", "hypothesis", "decision", "model", "because",
)


@dataclass
class Relationship:
    relation: str
    target: str


@dataclass
class ResearchArtifact:
    artifact_id: str
    title: str
    status: str
    created_at: str
    updated_at: str
    source_hash: str
    content_hash: str
    summary: str
    discoveries: list[str]
    hypotheses: list[str]
    open_questions: list[str]
    decisions: list[str]
    next_actions: list[str]
    evidence: list[str]
    relationships: list[Relationship]
    tags: list[str]
    quality_score: int
    duplicate_of: str | None = None


def _read_source(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    if sys.stdin.isatty():
        raise SystemExit("ต้องระบุ --input หรือส่งข้อความผ่าน stdin")
    return sys.stdin.read()


def _normalize_source(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        raise SystemExit("ไม่พบเนื้อหาสำหรับสกัดองค์ความรู้")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return raw

    if isinstance(payload, list):
        lines: list[str] = []
        for item in payload:
            if isinstance(item, dict):
                role = str(item.get("role", "message"))
                content = str(item.get("content", "")).strip()
                if content:
                    lines.append(f"{role}: {content}")
            elif isinstance(item, str):
                lines.append(item)
        return "\n\n".join(lines)

    if isinstance(payload, dict):
        messages = payload.get("messages")
        if isinstance(messages, list):
            return _normalize_source(json.dumps(messages, ensure_ascii=False))
        return json.dumps(payload, ensure_ascii=False, indent=2)
    return str(payload)


def _sentences(text: str) -> list[str]:
    compact = re.sub(r"[ \t]+", " ", text)
    parts = re.split(r"(?<=[.!?。！？])\s+|\n+", compact)
    return [p.strip(" -•\t") for p in parts if len(p.strip()) >= 4]


def _is_low_value(sentence: str) -> bool:
    normalized = sentence.strip().lower()
    return any(re.match(pattern, normalized, re.IGNORECASE) for pattern in LOW_VALUE_PATTERNS)


def _knowledge_score(sentence: str) -> int:
    score = 0
    lower = sentence.lower()
    score += sum(2 for signal in KNOWLEDGE_SIGNALS if signal in lower)
    if "?" in sentence or "หรือไม่" in sentence or "อย่างไร" in sentence:
        score += 1
    if len(sentence) >= 40:
        score += 1
    if re.search(r"\b[A-Z]{2,10}-\d{2,}\b", sentence):
        score += 2
    if _is_low_value(sentence):
        score -= 10
    return score


def _filter_sentences(sentences: list[str], threshold: int = 1) -> list[str]:
    return [s for s in sentences if _knowledge_score(s) >= threshold]


def _unique(items: Iterable[str], limit: int = 10) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = re.sub(r"\W+", "", item).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
        if len(result) >= limit:
            break
    return result


def _select(sentences: list[str], keywords: tuple[str, ...], limit: int) -> list[str]:
    return _unique(
        (s for s in sentences if any(k.lower() in s.lower() for k in keywords)),
        limit,
    )


def _content_hash(parts: Iterable[str]) -> str:
    canonical = "\n".join(sorted(re.sub(r"\s+", " ", p.strip()).lower() for p in parts if p.strip()))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _parse_front_matter(content: str) -> dict[str, str]:
    if not content.startswith("---\n"):
        return {}
    end = content.find("\n---", 4)
    if end < 0:
        return {}
    result: dict[str, str] = {}
    for line in content[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"')
    return result


def _find_duplicate(output_dir: Path, content_hash: str) -> str | None:
    for path in output_dir.glob("RES-*.md"):
        metadata = _parse_front_matter(path.read_text(encoding="utf-8"))
        if metadata.get("content_hash") == f"sha256:{content_hash}":
            return metadata.get("artifact_id") or path.stem
    return None


def _quality_score(artifact: ResearchArtifact) -> int:
    score = 20
    score += min(len(artifact.discoveries) * 5, 20)
    score += min(len(artifact.hypotheses) * 4, 12)
    score += min(len(artifact.open_questions) * 3, 9)
    score += min(len(artifact.decisions) * 5, 15)
    score += min(len(artifact.evidence) * 6, 18)
    score += min(len(artifact.relationships) * 3, 6)
    return min(score, 100)


def _deterministic_extract(
    text: str,
    title: str,
    status: str,
    tags: list[str],
    evidence: list[str],
    relationships: list[Relationship],
    output_dir: Path,
) -> ResearchArtifact:
    all_sentences = _sentences(text)
    sentences = _filter_sentences(all_sentences)
    discoveries = _select(sentences, ("ค้นพบ", "สรุป", "แนวคิด", "หลักการ", "ควร", "ต้อง", "คือ", "แยก"), 12)
    hypotheses = _select(sentences, ("สมมติฐาน", "อาจ", "น่าจะ", "คิดว่า", "เสนอ", "hypothesis"), 10)
    questions = _select(sentences, ("?", "หรือไม่", "อย่างไร", "อะไร", "ทำไม"), 10)
    decisions = _select(sentences, ("ตัดสินใจ", "ยืนยัน", "ตกลง", "ใช้", "เลือก", "เริ่ม"), 10)
    next_actions = _select(sentences, ("ต่อไป", "ขั้นถัดไป", "สร้าง", "เพิ่ม", "อัปเดต", "ทดลอง", "ทำต่อ"), 10)

    summary_candidates = discoveries or sentences
    summary = " ".join(summary_candidates[:3])[:700].rstrip()
    if len(summary) == 700:
        summary = summary[:-3].rstrip() + "..."

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    knowledge_hash = _content_hash(discoveries + hypotheses + questions + decisions + next_actions)
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    day = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    artifact_id = f"RES-{day}-{digest[:8].upper()}"
    duplicate_of = _find_duplicate(output_dir, knowledge_hash)

    artifact = ResearchArtifact(
        artifact_id=artifact_id,
        title=title,
        status=status,
        created_at=now,
        updated_at=now,
        source_hash=f"sha256:{digest}",
        content_hash=f"sha256:{knowledge_hash}",
        summary=summary or "ยังไม่พบสาระที่ผ่าน Knowledge Filter",
        discoveries=discoveries,
        hypotheses=hypotheses,
        open_questions=questions,
        decisions=decisions,
        next_actions=next_actions,
        evidence=evidence,
        relationships=relationships,
        tags=tags,
        quality_score=0,
        duplicate_of=duplicate_of,
    )
    artifact.quality_score = _quality_score(artifact)
    return artifact


def _provider_extract(text: str, base: ResearchArtifact) -> ResearchArtifact:
    endpoint = os.getenv("CURATOR_API_URL")
    model = os.getenv("CURATOR_MODEL")
    api_key = os.getenv("CURATOR_API_KEY")
    if not endpoint or not model:
        return base

    prompt = {
        "task": "Extract a concise research knowledge diff from the conversation.",
        "language": "Thai",
        "schema": {
            "summary": "string",
            "discoveries": ["string"],
            "hypotheses": ["string"],
            "open_questions": ["string"],
            "decisions": ["string"],
            "next_actions": ["string"],
        },
        "constraints": [
            "Do not invent facts.",
            "Keep rejected or uncertain ideas under hypotheses or open_questions.",
            "Return JSON only.",
        ],
        "conversation": text,
    }
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a research curator."},
            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
        ],
        "temperature": 0.1,
    }).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        enriched = json.loads(payload["choices"][0]["message"]["content"])
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError) as exc:
        print(f"คำเตือน: provider enrichment ล้มเหลว: {exc}", file=sys.stderr)
        return base

    for field in ("summary", "discoveries", "hypotheses", "open_questions", "decisions", "next_actions"):
        value = enriched.get(field)
        if value:
            setattr(base, field, value)
    base.quality_score = _quality_score(base)
    return base


def _yaml_scalar(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _render_markdown(artifact: ResearchArtifact) -> str:
    def section(title: str, items: list[str]) -> str:
        body = "\n".join(f"- {item}" for item in items) if items else "- ยังไม่มีรายการ"
        return f"## {title}\n\n{body}\n"

    tags = ", ".join(_yaml_scalar(tag) for tag in artifact.tags)
    relations = ", ".join(
        _yaml_scalar(f"{r.relation}:{r.target}") for r in artifact.relationships
    )
    duplicate = artifact.duplicate_of or ""
    return (
        "---\n"
        f"artifact_id: {_yaml_scalar(artifact.artifact_id)}\n"
        f"title: {_yaml_scalar(artifact.title)}\n"
        f"status: {_yaml_scalar(artifact.status)}\n"
        f"created_at: {_yaml_scalar(artifact.created_at)}\n"
        f"updated_at: {_yaml_scalar(artifact.updated_at)}\n"
        f"source_hash: {_yaml_scalar(artifact.source_hash)}\n"
        f"content_hash: {_yaml_scalar(artifact.content_hash)}\n"
        f"quality_score: {artifact.quality_score}\n"
        f"duplicate_of: {_yaml_scalar(duplicate)}\n"
        f"tags: [{tags}]\n"
        f"relationships: [{relations}]\n"
        "---\n\n"
        f"# {artifact.artifact_id} — {artifact.title}\n\n"
        "## Summary\n\n"
        f"{artifact.summary}\n\n"
        + section("Discoveries", artifact.discoveries) + "\n"
        + section("Hypotheses", artifact.hypotheses) + "\n"
        + section("Open Questions", artifact.open_questions) + "\n"
        + section("Decisions", artifact.decisions) + "\n"
        + section("Next Actions", artifact.next_actions) + "\n"
        + section("Evidence", artifact.evidence) + "\n"
        + section("Relationships", [f"`{r.relation}` → `{r.target}`" for r in artifact.relationships])
        + "\n## Provenance\n\n"
        f"- Source hash: `{artifact.source_hash}`\n"
        f"- Knowledge content hash: `{artifact.content_hash}`\n"
        f"- Generated at: `{artifact.created_at}`\n"
        "- Generator: `Research Curator v0.2.0`\n"
    )


def _write_artifact(output_dir: Path, artifact: ResearchArtifact, allow_duplicate: bool) -> Path:
    if artifact.duplicate_of and not allow_duplicate:
        raise SystemExit(
            f"พบ Knowledge Diff ซ้ำกับ {artifact.duplicate_of}; ใช้ --allow-duplicate หากต้องการบันทึก"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{artifact.artifact_id}_{re.sub(r'[^A-Za-z0-9ก-๙]+', '_', artifact.title).strip('_')}.md"
    target = output_dir / filename
    if target.exists():
        raise SystemExit(f"Artifact มีอยู่แล้ว: {target}")
    target.write_text(_render_markdown(artifact), encoding="utf-8")
    return target


def _update_index(output_dir: Path) -> Path:
    artifacts = sorted(output_dir.glob("RES-*.md"))
    lines = [
        "# Research Artifact Index", "", "ดัชนีนี้สร้างโดย Research Curator", "",
        "| Artifact | Title | Status | Quality | Duplicate |",
        "|---|---|---|---:|---|",
    ]
    for path in artifacts:
        metadata = _parse_front_matter(path.read_text(encoding="utf-8"))
        artifact_id = metadata.get("artifact_id", path.stem)
        lines.append(
            f"| [{artifact_id}]({path.name}) | {metadata.get('title', '-')} | "
            f"{metadata.get('status', '-')} | {metadata.get('quality_score', '-')} | "
            f"{metadata.get('duplicate_of', '') or '-'} |"
        )
    index = output_dir / "README.md"
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return index


def _validate(output_dir: Path) -> int:
    failures: list[str] = []
    known_ids: set[str] = set()
    records: list[tuple[Path, dict[str, str], str]] = []
    required = (
        "artifact_id", "title", "status", "created_at", "updated_at",
        "source_hash", "content_hash", "quality_score",
    )
    for path in output_dir.glob("RES-*.md"):
        content = path.read_text(encoding="utf-8")
        metadata = _parse_front_matter(content)
        records.append((path, metadata, content))
        artifact_id = metadata.get("artifact_id")
        if artifact_id:
            known_ids.add(artifact_id)
        for field in required:
            if not metadata.get(field):
                failures.append(f"{path}: missing {field}")
        status = metadata.get("status")
        if status and status not in STATUS_VALUES:
            failures.append(f"{path}: invalid status {status}")
        try:
            quality = int(metadata.get("quality_score", "-1"))
            if not 0 <= quality <= 100:
                raise ValueError
        except ValueError:
            failures.append(f"{path}: invalid quality_score")

    for path, metadata, _content in records:
        relationship_line = metadata.get("relationships", "")
        for relation, target in re.findall(r'([a-z_]+):([A-Za-z0-9._/-]+)', relationship_line):
            if relation not in RELATION_VALUES:
                failures.append(f"{path}: invalid relation {relation}")
            if target.startswith("RES-") and target not in known_ids:
                failures.append(f"{path}: unresolved relationship target {target}")
        duplicate = metadata.get("duplicate_of", "")
        if duplicate and duplicate.startswith("RES-") and duplicate not in known_ids:
            failures.append(f"{path}: unresolved duplicate_of {duplicate}")

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"Validated {len(records)} artifact(s)")
    return 0


def _promote(path: Path, new_status: str, evidence: list[str]) -> None:
    content = path.read_text(encoding="utf-8")
    metadata = _parse_front_matter(content)
    old_status = metadata.get("status")
    if old_status not in STATUS_VALUES:
        raise SystemExit(f"ไม่พบสถานะเดิมที่ถูกต้องใน {path}")
    if STATUS_FLOW.index(new_status) < STATUS_FLOW.index(old_status) and new_status != "deprecated":
        raise SystemExit(f"ห้ามลดสถานะจาก {old_status} เป็น {new_status}")
    if new_status in {"validated", "standardized"} and not evidence and "## Evidence\n\n- ยังไม่มีรายการ" in content:
        raise SystemExit(f"การเลื่อนเป็น {new_status} ต้องมี Evidence")

    content = re.sub(
        r'^status:\s*"?[^"\n]+"?$',
        f"status: {_yaml_scalar(new_status)}",
        content,
        count=1,
        flags=re.MULTILINE,
    )
    content = re.sub(
        r'^updated_at:\s*"?[^"\n]+"?$',
        f"updated_at: {_yaml_scalar(dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat())}",
        content,
        count=1,
        flags=re.MULTILINE,
    )
    if evidence:
        evidence_block = "\n".join(f"- {item}" for item in evidence)
        content = content.replace("## Evidence\n\n- ยังไม่มีรายการ", f"## Evidence\n\n{evidence_block}")
    path.write_text(content, encoding="utf-8")


def _parse_relationship(values: list[str]) -> list[Relationship]:
    result: list[Relationship] = []
    for value in values:
        if ":" not in value:
            raise SystemExit("--relate ต้องอยู่ในรูป relation:TARGET")
        relation, target = value.split(":", 1)
        if relation not in RELATION_VALUES:
            raise SystemExit(f"relation ไม่รองรับ: {relation}")
        if not target.strip():
            raise SystemExit("relationship target ห้ามว่าง")
        result.append(Relationship(relation, target.strip()))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Conversation-to-research knowledge curator")
    sub = parser.add_subparsers(dest="command", required=True)

    curate = sub.add_parser("curate", help="สกัดบทสนทนาเป็น Research Artifact")
    curate.add_argument("--input", help="ไฟล์ข้อความหรือ JSON; ไม่ระบุจะอ่าน stdin")
    curate.add_argument("--output", default="research/artifacts", help="โฟลเดอร์ผลลัพธ์")
    curate.add_argument("--title", required=True)
    curate.add_argument("--status", default="new", choices=STATUS_FLOW)
    curate.add_argument("--tag", action="append", default=[])
    curate.add_argument("--evidence", action="append", default=[])
    curate.add_argument("--relate", action="append", default=[], help="relation:TARGET")
    curate.add_argument("--provider", action="store_true")
    curate.add_argument("--allow-duplicate", action="store_true")
    curate.add_argument("--min-quality", type=int, default=20)

    index = sub.add_parser("index", help="สร้างดัชนี Research Artifacts")
    index.add_argument("--output", default="research/artifacts")

    validate = sub.add_parser("validate", help="ตรวจ metadata และ relationships")
    validate.add_argument("--output", default="research/artifacts")

    promote = sub.add_parser("promote", help="เลื่อน Truth Status พร้อม Evidence")
    promote.add_argument("artifact")
    promote.add_argument("--to", required=True, choices=STATUS_FLOW)
    promote.add_argument("--evidence", action="append", default=[])
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "curate":
        output_dir = Path(args.output)
        source = _normalize_source(_read_source(args.input))
        artifact = _deterministic_extract(
            source,
            args.title,
            args.status,
            args.tag,
            args.evidence,
            _parse_relationship(args.relate),
            output_dir,
        )
        if args.provider:
            artifact = _provider_extract(source, artifact)
        if artifact.quality_score < args.min_quality:
            raise SystemExit(
                f"Knowledge Filter ปฏิเสธ Artifact: quality_score={artifact.quality_score} "
                f"ต่ำกว่า min-quality={args.min_quality}"
            )
        path = _write_artifact(output_dir, artifact, args.allow_duplicate)
        index = _update_index(output_dir)
        print(json.dumps({
            "artifact": str(path),
            "index": str(index),
            "metadata": asdict(artifact),
        }, ensure_ascii=False, indent=2))
        return 0
    if args.command == "index":
        print(_update_index(Path(args.output)))
        return 0
    if args.command == "validate":
        return _validate(Path(args.output))
    if args.command == "promote":
        _promote(Path(args.artifact), args.to, args.evidence)
        print(args.artifact)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
