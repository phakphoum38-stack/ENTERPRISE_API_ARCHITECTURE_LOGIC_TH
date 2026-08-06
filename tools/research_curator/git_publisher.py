#!/usr/bin/env python3
"""Validated Research Artifact Git publisher.

Creates a branch, stages selected artifacts and generated indexes/graphs, commits,
pushes, and optionally opens a draft pull request through the GitHub CLI.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ALLOWED_STATUS = {"observed", "repeated", "validated", "standardized"}


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=check, text=True, capture_output=True)


def require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"ไม่พบคำสั่งที่จำเป็น: {name}")


def metadata(path: Path) -> dict[str, str]:
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        raise SystemExit(f"Artifact ไม่มี front matter: {path}")
    end = content.find("\n---", 4)
    if end < 0:
        raise SystemExit(f"Artifact front matter ไม่สมบูรณ์: {path}")
    result: dict[str, str] = {}
    for line in content[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"')
    return result


def validate_publishable(path: Path, allow_hypothesis: bool) -> dict[str, str]:
    data = metadata(path)
    required = ("artifact_id", "title", "status", "source_hash", "content_hash", "quality_score")
    missing = [key for key in required if not data.get(key)]
    if missing:
        raise SystemExit(f"{path}: ขาด metadata {', '.join(missing)}")
    status = data["status"]
    if status not in ALLOWED_STATUS and not allow_hypothesis:
        raise SystemExit(
            f"{path}: status={status} ยังไม่พร้อม publish; ใช้ --allow-hypothesis เมื่อยอมรับความเสี่ยง"
        )
    try:
        quality = int(data["quality_score"])
    except ValueError as exc:
        raise SystemExit(f"{path}: quality_score ไม่ใช่จำนวนเต็ม") from exc
    if quality < 45:
        raise SystemExit(f"{path}: quality_score={quality} ต่ำกว่า publish gate 45")
    if data.get("duplicate_of"):
        raise SystemExit(f"{path}: เป็น duplicate ของ {data['duplicate_of']}")
    return data


def slug(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9ก-๙]+", "-", value).strip("-").lower()
    return normalized[:48] or "research-update"


def ensure_clean_worktree() -> None:
    result = run(["git", "status", "--porcelain"])
    if result.stdout.strip():
        raise SystemExit("Working tree ไม่สะอาด กรุณา commit/stash การเปลี่ยนแปลงเดิมก่อน")


def publish(args: argparse.Namespace) -> dict[str, object]:
    require_command("git")
    if args.open_pr:
        require_command("gh")

    artifact_paths = [Path(value).resolve() for value in args.artifact]
    artifacts = [validate_publishable(path, args.allow_hypothesis) for path in artifact_paths]
    ensure_clean_worktree()

    current_branch = run(["git", "branch", "--show-current"]).stdout.strip()
    run(["git", "fetch", "origin", args.base])
    run(["git", "switch", args.base])
    run(["git", "pull", "--ff-only", "origin", args.base])

    first = artifacts[0]
    branch = args.branch or f"research/{slug(first['artifact_id'] + '-' + first['title'])}"
    run(["git", "switch", "-c", branch])

    paths_to_stage = [str(path) for path in artifact_paths]
    for extra in args.include:
        paths_to_stage.append(extra)
    run(["git", "add", "--", *paths_to_stage])

    staged = run(["git", "diff", "--cached", "--name-only"]).stdout.splitlines()
    if not staged:
        raise SystemExit("ไม่มีการเปลี่ยนแปลงสำหรับ commit")

    commit_message = args.message or f"research: publish {first['artifact_id']}"
    run(["git", "commit", "-m", commit_message])
    run(["git", "push", "-u", "origin", branch])

    pr_url = None
    if args.open_pr:
        title = args.pr_title or f"research: {first['title']}"
        body_lines = [
            "## Research publication",
            "",
            *[f"- `{item['artifact_id']}` — {item['title']} ({item['status']})" for item in artifacts],
            "",
            "## Validation",
            "",
            "- Metadata gate passed",
            "- Quality gate passed",
            "- Duplicate gate passed",
        ]
        command = [
            "gh", "pr", "create",
            "--base", args.base,
            "--head", branch,
            "--title", title,
            "--body", "\n".join(body_lines),
        ]
        if args.draft:
            command.append("--draft")
        pr_url = run(command).stdout.strip()

    return {
        "previous_branch": current_branch,
        "branch": branch,
        "commit": run(["git", "rev-parse", "HEAD"]).stdout.strip(),
        "staged_files": staged,
        "pr_url": pr_url,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Publish validated research artifacts through Git and GitHub CLI")
    parser.add_argument("--artifact", action="append", required=True, help="Artifact path; ใช้ซ้ำได้")
    parser.add_argument("--include", action="append", default=[], help="ไฟล์ index/graph เพิ่มเติม; ใช้ซ้ำได้")
    parser.add_argument("--base", default="main")
    parser.add_argument("--branch")
    parser.add_argument("--message")
    parser.add_argument("--open-pr", action="store_true")
    parser.add_argument("--draft", action="store_true")
    parser.add_argument("--pr-title")
    parser.add_argument("--allow-hypothesis", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = publish(args)
    except subprocess.CalledProcessError as exc:
        if exc.stdout:
            print(exc.stdout, file=sys.stderr)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        return exc.returncode or 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
