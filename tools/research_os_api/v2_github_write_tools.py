#!/usr/bin/env python3
"""Approval-gated GitHub branch-file and PR-comment writes (Brain Phase 6)."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import asdict
from pathlib import PurePosixPath
from typing import Any

from v2_tool_registry import ToolDefinition, ToolRegistry

CONTRACT = "brain-github-write-tools-phase-6"
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}$")
BRANCH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,199}$")
SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
MAX_CONTENT = 1024 * 1024
MAX_COMMENT = 10000

TOOLS: tuple[ToolDefinition, ...] = (
    ToolDefinition(
        "github.branch.file.upsert", "1.0.0", "GitHub Branch File Upsert",
        "Create or update one UTF-8 text file on an explicitly non-protected GitHub branch.",
        ("github_write", "github_branch_file_write", "github_commit_create"),
        permissions=("github.write",), mutating=True, network=True, secret_access=True,
        idempotent=False, supports_dry_run=True,
    ),
    ToolDefinition(
        "github.pull_request.comment", "1.0.0", "GitHub Pull Request Comment",
        "Add one comment to an existing GitHub pull request without changing code or PR state.",
        ("github_write", "github_pull_request_comment"), permissions=("github.write",),
        mutating=True, network=True, secret_access=True, idempotent=False, supports_dry_run=True,
    ),
)
GITHUB_WRITE_TOOL_DEFINITIONS = TOOLS
GITHUB_WRITE_TOOLS_CONTRACT = CONTRACT
GitHubMutationProvider = Callable[[str, Mapping[str, Any]], Mapping[str, Any]]


def _token() -> str:
    value = os.getenv("RESEARCH_OS_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN") or ""
    if not value.strip(): raise RuntimeError("GitHub write credential is not configured")
    return value.strip()


def _request(method: str, path: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
    headers = {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {_token()}",
               "Content-Type": "application/json", "User-Agent": "research-os-api",
               "X-GitHub-Api-Version": "2022-11-28"}
    req = urllib.request.Request(f"https://api.github.com{path}", headers=headers,
                                 data=json.dumps(dict(payload)).encode(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            value = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub write request failed with HTTP {exc.code}") from exc
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"GitHub write request failed: {type(exc).__name__}") from exc
    if not isinstance(value, Mapping): raise RuntimeError("GitHub write response has an invalid shape")
    return value


def _default_provider(action: str, p: Mapping[str, Any]) -> Mapping[str, Any]:
    owner, repo = str(p["repository"]).split("/", 1)
    base = f"/repos/{urllib.parse.quote(owner, safe='')}/{urllib.parse.quote(repo, safe='')}"
    if action == "file_upsert":
        path = "/".join(urllib.parse.quote(x, safe="") for x in str(p["path"]).split("/"))
        body: dict[str, Any] = {"message": p["message"], "branch": p["branch"],
                                "content": base64.b64encode(str(p["content"]).encode()).decode()}
        if p.get("expected_sha"): body["sha"] = p["expected_sha"]
        result = _request("PUT", f"{base}/contents/{path}", body)
        content = result.get("content") if isinstance(result.get("content"), Mapping) else {}
        commit = result.get("commit") if isinstance(result.get("commit"), Mapping) else {}
        return {"content_sha": content.get("sha"), "commit_sha": commit.get("sha"),
                "commit_url": commit.get("html_url")}
    if action == "pr_comment":
        result = _request("POST", f"{base}/issues/{int(p['pr_number'])}/comments", {"body": p["comment"]})
        return {"comment_id": result.get("id"), "comment_url": result.get("html_url")}
    raise ValueError(f"unsupported GitHub mutation provider action: {action}")


def _repo(value: Any) -> str:
    x = str(value or "").strip()
    if not REPO_RE.fullmatch(x) or x.startswith(".") or "/." in x:
        raise ValueError("repository must use owner/name format")
    return x


def _branch(value: Any) -> str:
    x = str(value or "").strip()
    if not BRANCH_RE.fullmatch(x) or ".." in x or x.endswith("/"):
        raise ValueError("invalid branch name")
    return x


def _path(value: Any) -> str:
    raw = str(value or "").strip().replace("\\", "/"); p = PurePosixPath(raw)
    if not raw or raw.startswith("/") or ".." in p.parts or "." in p.parts or len(raw) > 512:
        raise ValueError("repository path must be a relative normalized path")
    name = p.name.casefold()
    if (name.startswith(".env") and name != ".env.example") or name in {
        "credentials.json", "client_secret.json", "secrets.json", "id_rsa", "id_ed25519"
    } or p.suffix.casefold() in {".key", ".p12", ".pfx"}:
        raise ValueError("secret-bearing repository path is blocked")
    return raw


def _fingerprint(values: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(dict(values), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class GitHubWriteTools:
    def __init__(self, provider: GitHubMutationProvider = _default_provider, *,
                 blocked_branches: tuple[str, ...] = ("main", "master", "stable", "production", "prod"),
                 blocked_prefixes: tuple[str, ...] = ("release/", "deploy/")) -> None:
        if not callable(provider): raise ValueError("GitHub mutation provider must be callable")
        self.provider = provider
        self.blocked_branches = tuple(x.casefold() for x in blocked_branches)
        self.blocked_prefixes = tuple(x.casefold() for x in blocked_prefixes)

    def _guard(self, branch: str) -> None:
        x = branch.casefold()
        if x in self.blocked_branches or any(x.startswith(p) for p in self.blocked_prefixes):
            raise ValueError(f"protected GitHub branch is blocked by Phase 6 policy: {branch}")

    def file_upsert(self, payload: Mapping[str, Any], *, dry_run: bool) -> dict[str, Any]:
        repo, branch, path = _repo(payload.get("repository")), _branch(payload.get("branch")), _path(payload.get("path"))
        self._guard(branch)
        content, message = payload.get("content"), str(payload.get("message") or "").strip()
        if not isinstance(content, str) or len(content.encode()) > MAX_CONTENT:
            raise ValueError("GitHub file upsert requires UTF-8 text up to 1 MiB")
        if not 1 <= len(message) <= 240: raise ValueError("commit message must contain 1-240 characters")
        expected = str(payload.get("expected_sha") or "").strip() or None; create = bool(payload.get("create", False))
        if create and expected: raise ValueError("create=true cannot include expected_sha")
        if not create and not expected: raise ValueError("updating an existing GitHub file requires expected_sha")
        if expected and not SHA_RE.fullmatch(expected): raise ValueError("expected_sha must be a 40-character Git blob SHA")
        values = {"repository": repo, "branch": branch, "path": path,
                  "content_sha256": hashlib.sha256(content.encode()).hexdigest(), "message": message,
                  "expected_sha": expected, "create": create}
        fp = _fingerprint(values)
        plan = {"contract": CONTRACT, **values, "approval_fingerprint": fp, "write_action": "file_upsert",
                "merge": False, "release": False, "deployment": False, "applied": False}
        if dry_run: return plan
        if str(payload.get("approval_fingerprint") or "").strip() != fp:
            raise ValueError("GitHub file upsert requires matching approval_fingerprint from dry-run")
        result = self.provider("file_upsert", {"repository": repo, "branch": branch, "path": path,
                                               "content": content, "message": message,
                                               "expected_sha": expected, "create": create})
        if not isinstance(result, Mapping): raise TypeError("GitHub mutation provider must return a mapping")
        return {**plan, "applied": True, "result": dict(result)}

    def pr_comment(self, payload: Mapping[str, Any], *, dry_run: bool) -> dict[str, Any]:
        repo, number, comment = _repo(payload.get("repository")), int(payload.get("pr_number") or 0), payload.get("comment")
        if number < 1 or not isinstance(comment, str) or not comment.strip() or len(comment) > MAX_COMMENT:
            raise ValueError("valid pr_number and 1-10000 character comment are required")
        values = {"repository": repo, "pr_number": number,
                  "comment_sha256": hashlib.sha256(comment.encode()).hexdigest()}
        fp = _fingerprint(values)
        plan = {"contract": CONTRACT, **values, "approval_fingerprint": fp, "write_action": "pr_comment",
                "code_changed": False, "pr_state_changed": False, "applied": False}
        if dry_run: return plan
        if str(payload.get("approval_fingerprint") or "").strip() != fp:
            raise ValueError("GitHub PR comment requires matching approval_fingerprint from dry-run")
        result = self.provider("pr_comment", {"repository": repo, "pr_number": number, "comment": comment})
        if not isinstance(result, Mapping): raise TypeError("GitHub mutation provider must return a mapping")
        return {**plan, "applied": True, "result": dict(result)}

    def adapter(self, tool_id: str):
        if tool_id == "github.branch.file.upsert":
            def upsert(action: str, payload: Mapping[str, Any], dry_run: bool):
                if action != "upsert": raise ValueError(f"unsupported github.branch.file.upsert action: {action}")
                return self.file_upsert(payload, dry_run=dry_run)
            return upsert
        if tool_id == "github.pull_request.comment":
            def comment(action: str, payload: Mapping[str, Any], dry_run: bool):
                if action != "comment": raise ValueError(f"unsupported github.pull_request.comment action: {action}")
                return self.pr_comment(payload, dry_run=dry_run)
            return comment
        raise ValueError(f"unsupported GitHub write tool: {tool_id}")

    def status(self) -> dict[str, Any]:
        return {"contract": CONTRACT, "tool_count": len(TOOLS), "required_permission": "github.write",
                "network": True, "secret_access": True, "real_mutations_require_controller_approval": True,
                "approval_fingerprint_required": True, "blocked_branches": list(self.blocked_branches),
                "blocked_prefixes": list(self.blocked_prefixes), "merge_available": False,
                "delete_available": False, "workflow_dispatch_available": False, "tag_available": False,
                "release_available": False, "deployment_available": False}


def install_github_write_tools(registry: ToolRegistry, *, provider: GitHubMutationProvider = _default_provider,
                               blocked_branches: tuple[str, ...] = ("main", "master", "stable", "production", "prod"),
                               blocked_prefixes: tuple[str, ...] = ("release/", "deploy/")) -> GitHubWriteTools:
    pack = GitHubWriteTools(provider, blocked_branches=blocked_branches, blocked_prefixes=blocked_prefixes)
    for d in TOOLS:
        try: existing = registry.get(d.tool_id)
        except ValueError: registry.register(d)
        else:
            if asdict(existing) != asdict(d): raise ValueError(f"GitHub write tool definition collision: {d.tool_id}")
        try: registry.register_adapter(d.tool_id, pack.adapter(d.tool_id))
        except ValueError as exc:
            if "already registered" not in str(exc): raise
            registry.register_adapter(d.tool_id, pack.adapter(d.tool_id), replace=True)
    return pack
