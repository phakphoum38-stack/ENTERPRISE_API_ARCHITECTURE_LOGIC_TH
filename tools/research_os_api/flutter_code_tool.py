from __future__ import annotations

"""Owner-only local Flutter code editing service.

The service operates only inside an explicit allowlisted project root, uses a
content SHA to prevent TOCTOU overwrites, previews unified diffs before writes,
and validates every applied change with the external Flutter tool.
"""

import hashlib
import json
import os
import subprocess
import time
from difflib import unified_diff
from pathlib import Path
from typing import Any

MAX_FILE_BYTES = 1024 * 1024
MAX_LIST_ITEMS = 2000
BLOCKED_PARTS = {".git", ".dart_tool", "build", "__pycache__"}
BLOCKED_PREFIXES = (".github/workflows/",)
TEXT_EXTENSIONS = {
    ".dart", ".yaml", ".yml", ".json", ".md", ".txt", ".py", ".toml",
    ".xml", ".gradle", ".properties", ".html", ".css", ".js", ".ts",
}

def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def _projects(root: Path) -> dict[str, Path]:
    configured = (os.environ.get("RESEARCH_OS_CODE_PROJECTS") or "").strip()
    result: dict[str, Path] = {}
    if configured:
        for item in configured.split(","):
            if "=" not in item:
                continue
            name, relative = item.split("=", 1)
            name, relative = name.strip(), relative.strip()
            if name and relative:
                result[name] = (root / relative).resolve()
    if not result:
        result["research_os_flutter"] = (root / "apps" / "research_os_flutter").resolve()
    return result

def _root() -> Path:
    configured = (os.environ.get("RESEARCH_OS_CODE_ROOT") or "").strip()
    return Path(configured).resolve() if configured else Path(__file__).resolve().parents[2]

def project_map() -> dict[str, str]:
    root = _root()
    return {name: str(path.relative_to(root)) for name, path in _projects(root).items() if path.is_dir()}

def _project(name: str) -> tuple[Path, Path]:
    root = _root()
    projects = _projects(root)
    if name not in projects:
        raise ValueError("unknown code project")
    project = projects[name]
    if not project.is_dir():
        raise ValueError("code project is not available")
    try:
        project.relative_to(root)
    except ValueError as exc:
        raise ValueError("code project escapes code root") from exc
    return root, project

def _safe_path(project: Path, relative: str) -> Path:
    value = relative.replace("\\", "/").strip()
    if not value or value.startswith("/") or ":" in value.split("/")[0]:
        raise ValueError("absolute paths are not allowed")
    candidate = (project / value).resolve()
    try:
        candidate.relative_to(project)
    except ValueError as exc:
        raise ValueError("path escapes project root") from exc
    rel = candidate.relative_to(project).as_posix()
    if any(part in BLOCKED_PARTS for part in candidate.relative_to(project).parts):
        raise ValueError("path is protected")
    if any(rel.startswith(prefix) for prefix in BLOCKED_PREFIXES):
        raise ValueError("workflow files are protected")
    if candidate.suffix.lower() not in TEXT_EXTENSIONS:
        raise ValueError("unsupported source file type")
    return candidate

def list_files(project_name: str, query: str = "") -> dict[str, Any]:
    _, project = _project(project_name)
    query = query.strip().casefold()
    items: list[dict[str, Any]] = []
    for path in project.rglob("*"):
        if len(items) >= MAX_LIST_ITEMS:
            break
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(project)
            _safe_path(project, rel.as_posix())
        except (ValueError, OSError):
            continue
        if query and query not in rel.as_posix().casefold():
            continue
        items.append({"path": rel.as_posix(), "bytes": path.stat().st_size})
    items.sort(key=lambda item: item["path"])
    return {"project": project_name, "items": items, "count": len(items)}

def read_file(project_name: str, relative: str) -> dict[str, Any]:
    _, project = _project(project_name)
    path = _safe_path(project, relative)
    data = path.read_bytes()
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("file is too large")
    content = data.decode("utf-8")
    return {
        "project": project_name,
        "path": path.relative_to(project).as_posix(),
        "content": content,
        "sha256": _sha(content),
        "bytes": len(data),
    }

def preview(project_name: str, relative: str, original_sha256: str, content: str) -> dict[str, Any]:
    current = read_file(project_name, relative)
    if current["sha256"] != original_sha256:
        raise RuntimeError("file changed since it was read; refresh before preview")
    if len(content.encode("utf-8")) > MAX_FILE_BYTES:
        raise ValueError("file is too large")
    before = current["content"].splitlines(keepends=True)
    after = content.splitlines(keepends=True)
    diff = "".join(unified_diff(
        before, after,
        fromfile=f"a/{current['path']}",
        tofile=f"b/{current['path']}",
    ))
    return {
        "project": project_name,
        "path": current["path"],
        "original_sha256": original_sha256,
        "new_sha256": _sha(content),
        "changed": content != current["content"],
        "diff": diff,
    }

def _run(command: list[str], cwd: Path, timeout: int) -> dict[str, Any]:
    started = time.time()
    completed = subprocess.run(
        command, cwd=str(cwd), capture_output=True, text=True,
        timeout=timeout, check=False,
    )
    return {
        "command": command,
        "exit_code": completed.returncode,
        "stdout": completed.stdout[-12000:],
        "stderr": completed.stderr[-12000:],
        "duration_seconds": round(time.time() - started, 3),
    }

def validate(project_name: str) -> dict[str, Any]:
    _, project = _project(project_name)
    flutter = (os.environ.get("RESEARCH_OS_FLUTTER_COMMAND") or "flutter").strip()
    analyze = _run([flutter, "analyze"], project, 300)
    if analyze["exit_code"] != 0:
        return {"ok": False, "steps": [analyze]}
    test = _run([flutter, "test"], project, 600)
    return {"ok": test["exit_code"] == 0, "steps": [analyze, test]}

def apply(project_name: str, relative: str, original_sha256: str, content: str, principal: str) -> dict[str, Any]:
    allowed = {
        item.strip().lower()
        for item in (os.environ.get("RESEARCH_OS_CODE_OWNER_IDS") or os.environ.get("RESEARCH_OS_OWNER_EMAILS") or "").split(",")
        if item.strip()
    }
    if not allowed or principal.strip().lower() not in allowed:
        raise PermissionError("OWNER authority is required for code changes")
    _, project = _project(project_name)
    path = _safe_path(project, relative)
    current = read_file(project_name, relative)
    if current["sha256"] != original_sha256:
        raise RuntimeError("file changed since it was read; refresh before apply")
    if len(content.encode("utf-8")) > MAX_FILE_BYTES:
        raise ValueError("file is too large")
    old_content = current["content"]
    if old_content == content:
        return {"applied": False, "validation": {"ok": True, "steps": []}, "sha256": original_sha256}
    temporary = path.with_suffix(path.suffix + ".research-os-tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)
    validation = validate(project_name)
    evidence_dir = _root() / "evidence" / "flutter-code-tool"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence = {
        "tool": "owner-flutter-code-tool",
        "principal": principal,
        "project": project_name,
        "path": current["path"],
        "before_sha256": original_sha256,
        "after_sha256": _sha(content),
        "validation": validation,
        "timestamp": time.time(),
    }
    if not validation["ok"]:
        rollback = path.with_suffix(path.suffix + ".research-os-rollback")
        rollback.write_text(old_content, encoding="utf-8")
        rollback.replace(path)
        evidence["rolled_back"] = True
        evidence["final_sha256"] = _sha(old_content)
    else:
        evidence["rolled_back"] = False
        evidence["final_sha256"] = _sha(content)
    evidence_path = evidence_dir / f"{int(time.time() * 1000)}.json"
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"applied": not evidence["rolled_back"], "rolled_back": evidence["rolled_back"], "evidence": str(evidence_path), "validation": validation, "sha256": evidence["final_sha256"]}
