#!/usr/bin/env python3
"""Research Curator CLI.

Transforms a conversation export or plain text into a versioned research artifact.
The deterministic mode works without external services. An optional provider adapter
can enrich the summary through a configurable HTTP endpoint.
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
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable


STATUS_VALUES = {
    "hypothesis",
    "observed",
    "repeated",
    "validated",
    "reference",
    "deprecated",
}


@dataclass
class ResearchArtifact:
    artifact_id: str
    title: str
    status: str
    created_at: str
    source_hash: str
    summary: str
    discoveries: list[str]
    hypotheses: list[str]
    open_questions: list[str]
    decisions: list[str]
    next_actions: list[str]
    tags: list[str]


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
    return [p.strip(" -•\t") for p in parts if len(p.strip()) >= 12]


def _unique(items: Iterable[str], limit: int = 8) -> list[str]:
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
    selected = [s for s in sentences if any(k.lower() in s.lower() for k in keywords)]
    return _unique(selected, limit)


def _deterministic_extract(text: str, title: str, status: str, tags: list[str]) -> ResearchArtifact:
    sentences = _sentences(text)
    discoveries = _select(
        sentences,
        ("ค้นพบ", "สรุป", "แนวคิด", "หลักการ", "ควร", "ต้อง", "คือ", "แยก"),
        10,
    )
    hypotheses = _select(
        sentences,
        ("สมมติฐาน", "อาจ", "น่าจะ", "คิดว่า", "เสนอ", "hypothesis"),
        8,
    )
    questions = _select(sentences, ("?", "หรือไม่", "อย่างไร", "อะไร", "ทำไม"), 8)
    decisions = _select(sentences, ("ตัดสินใจ", "ยืนยัน", "ตกลง", "ใช้", "เลือก", "เริ่ม"), 8)
    next_actions = _select(sentences, ("ต่อไป", "ขั้นถัดไป", "สร้าง", "เพิ่ม", "อัปเดต", "ทดลอง"), 8)

    summary_candidates = discoveries or sentences
    summary = " ".join(summary_candidates[:3])
    if len(summary) > 700:
        summary = summary[:697].rstrip() + "..."

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    day = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    artifact_id = f"RES-{day}-{digest[:8].upper()}"

    return ResearchArtifact(
        artifact_id=artifact_id,
        title=title,
        status=status,
        created_at=dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        source_hash=f"sha256:{digest}",
        summary=summary or "ยังไม่สามารถสรุปสาระสำคัญได้",
        discoveries=discoveries,
        hypotheses=hypotheses,
        open_questions=questions,
        decisions=decisions,
        next_actions=next_actions,
        tags=tags,
    )


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
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a research curator."},
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
            "temperature": 0.1,
        }
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
        content = payload["choices"][0]["message"]["content"]
        enriched = json.loads(content)
    except (urllib.error.URLError, KeyError, IndexError, json.JSONDecodeError) as exc:
        print(f"คำเตือน: provider enrichment ล้มเหลว: {exc}", file=sys.stderr)
        return base

    for field in (
        "summary",
        "discoveries",
        "hypotheses",
        "open_questions",
        "decisions",
        "next_actions",
    ):
        value = enriched.get(field)
        if value:
            setattr(base, field, value)
    return base


def _yaml_scalar(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _render_markdown(artifact: ResearchArtifact) -> str:
    def section(title: str, items: list[str]) -> str:
        body = "\n".join(f"- {item}" for item in items) if items else "- ยังไม่มีรายการ"
        return f"## {title}\n\n{body}\n"

    tags = ", ".join(_yaml_scalar(tag) for tag in artifact.tags)
    return (
        "---\n"
        f"artifact_id: {_yaml_scalar(artifact.artifact_id)}\n"
        f"title: {_yaml_scalar(artifact.title)}\n"
        f"status: {_yaml_scalar(artifact.status)}\n"
        f"created_at: {_yaml_scalar(artifact.created_at)}\n"
        f"source_hash: {_yaml_scalar(artifact.source_hash)}\n"
        f"tags: [{tags}]\n"
        "---\n\n"
        f"# {artifact.artifact_id} — {artifact.title}\n\n"
        "## Summary\n\n"
        f"{artifact.summary}\n\n"
        + section("Discoveries", artifact.discoveries)
        + "\n"
        + section("Hypotheses", artifact.hypotheses)
        + "\n"
        + section("Open Questions", artifact.open_questions)
        + "\n"
        + section("Decisions", artifact.decisions)
        + "\n"
        + section("Next Actions", artifact.next_actions)
        + "\n## Provenance\n\n"
        f"- Source hash: `{artifact.source_hash}`\n"
        f"- Generated at: `{artifact.created_at}`\n"
        "- Generator: `Research Curator v0.1.0`\n"
    )


def _write_artifact(output_dir: Path, artifact: ResearchArtifact) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{artifact.artifact_id}_{re.sub(r'[^A-Za-z0-9ก-๙]+', '_', artifact.title).strip('_')}.md"
    target = output_dir / filename
    target.write_text(_render_markdown(artifact), encoding="utf-8")
    return target


def _update_index(output_dir: Path) -> Path:
    artifacts = sorted(output_dir.glob("RES-*.md"))
    lines = ["# Research Artifact Index", "", "ดัชนีนี้สร้างโดย Research Curator", "", "| Artifact | Title | Status |", "|---|---|---|"]
    for path in artifacts:
        content = path.read_text(encoding="utf-8")
        artifact_id = re.search(r'^artifact_id:\s*"?([^"\n]+)', content, re.MULTILINE)
        title = re.search(r'^title:\s*"?([^"\n]+)', content, re.MULTILINE)
        status = re.search(r'^status:\s*"?([^"\n]+)', content, re.MULTILINE)
        lines.append(
            f"| [{artifact_id.group(1) if artifact_id else path.stem}]({path.name}) | "
            f"{title.group(1) if title else '-'} | {status.group(1) if status else '-'} |"
        )
    index = output_dir / "README.md"
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return index


def _validate(output_dir: Path) -> int:
    failures: list[str] = []
    required = ("artifact_id", "title", "status", "created_at", "source_hash")
    for path in output_dir.glob("RES-*.md"):
        content = path.read_text(encoding="utf-8")
        for field in required:
            if not re.search(rf"^{field}:\s*.+$", content, re.MULTILINE):
                failures.append(f"{path}: missing {field}")
        status_match = re.search(r'^status:\s*"?([^"\n]+)', content, re.MULTILINE)
        if status_match and status_match.group(1) not in STATUS_VALUES:
            failures.append(f"{path}: invalid status {status_match.group(1)}")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"Validated {len(list(output_dir.glob('RES-*.md')))} artifact(s)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Conversation-to-research knowledge curator")
    sub = parser.add_subparsers(dest="command", required=True)

    curate = sub.add_parser("curate", help="สกัดบทสนทนาเป็น Research Artifact")
    curate.add_argument("--input", help="ไฟล์ข้อความหรือ JSON; ไม่ระบุจะอ่าน stdin")
    curate.add_argument("--output", default="research/artifacts", help="โฟลเดอร์ผลลัพธ์")
    curate.add_argument("--title", required=True, help="ชื่อ Research Artifact")
    curate.add_argument("--status", default="hypothesis", choices=sorted(STATUS_VALUES))
    curate.add_argument("--tag", action="append", default=[], help="Tag; ใช้ซ้ำได้")
    curate.add_argument("--provider", action="store_true", help="ใช้ provider adapter จาก environment")

    index = sub.add_parser("index", help="สร้างดัชนี Research Artifacts")
    index.add_argument("--output", default="research/artifacts")

    validate = sub.add_parser("validate", help="ตรวจ metadata ของ Research Artifacts")
    validate.add_argument("--output", default="research/artifacts")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output_dir = Path(args.output)

    if args.command == "curate":
        source = _normalize_source(_read_source(args.input))
        artifact = _deterministic_extract(source, args.title, args.status, args.tag)
        if args.provider:
            artifact = _provider_extract(source, artifact)
        path = _write_artifact(output_dir, artifact)
        index = _update_index(output_dir)
        print(json.dumps({"artifact": str(path), "index": str(index), "metadata": asdict(artifact)}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "index":
        print(_update_index(output_dir))
        return 0
    if args.command == "validate":
        return _validate(output_dir)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
