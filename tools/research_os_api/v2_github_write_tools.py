#!/usr/bin/env python3
"""Approval-gated GitHub mutations for Research OS AI Brain.

Phase 6 exposes a deliberately small GitHub write surface: upsert one file on a
non-protected branch, or comment on an existing pull request. There is no merge,
delete, tag, release, workflow-dispatch or deployment action. Every real call is
mutating, networked and credential-bearing, so the HardenedExecutionController
requires the declared permission plus explicit approval before this adapter is
invoked. Dry-run plans never call the provider.
"""

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


GITHUB_WRITE_TOOLS_CONTRACT = "brain-github-write-tools-phase-6"
_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}$")
_BRANCH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,199}$")
_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_MAX_CONTENT_BYTES = 1024 * 1024
_MAX_COMMENT_CHARS = 10000


GITHUB_WRITE_TOOL_DEFINITIONS: tuple[ToolDefinition, ...] = (
    ToolDefinition(
        "github.branch.file.upsert",
        "1.0.0",
        "GitHub Branch File Upsert",
        "Create or update one UTF-8 text file on an explicitly non-protected GitHub branch.",
        ("github_write", "github_branch_file_write", "github_commit_create"),
        permissions=("github.write",),
        mutating=True,
        destructive=False,
        network=True,
        secret_access=True,
        idempotent=False,
        supports_dry_run=True,
    ),
    ToolDefinition(
        "github.pull_request.comment",
        "1.0.0",
        "GitHub Pull Request Comment",
        "Add one comment to an existing GitHub pull request without changing code or PR state.",
        ("github_write", "github_pull_request_comment"),
        permissions=("github.write",),
        mutating=True,
        destructive=False,
        network=True,
        secret_access=True,
        idempotent=False,
        supports_dry_run=True,
    ),
)


GitHubMutationProvider = Callable[[str, Mapping[str, Any]], Mapping[str, Any]]


def _token() -> str:
    value = os.getenv("RESEARCH_OS_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN") or ""
    if not value.strip():
        raise RuntimeError("GitHub write credential is not configured")
    return value.strip()


def _headers() -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {_token()}",
        "Content-Type": "application/json",
        "User-Agent": "research-os-api",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _request_json(method: str, path: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        headers=_headers(),
        data=json.dumps(dict(payload)).encode("utf-8"),
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            decoded = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub write request failed with HTTP {exc.code}") from exc
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"GitHub write request failed: {type(exc).__name__}") from exc
    if not isinstance(decoded, Mapping):
        raise RuntimeError("GitHub write response has an invalid shape")
    return decoded


def _default_provider(action: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
    repository = str(payload["repository"])
    owner, repo = repository.split("/", 1)
    owner_q = urllib.parse.quote(owner, safe="")
    repo_q = urllib.parse.quote(repo, safe="")
    if action == "file_upsert":
        path = str(payload["path"])
        encoded_path = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
        body: dict[str, Any] = {
            "message": payload["message"],
            "content": base64.b64encode(str(payload["content"]).encode("utf-8")).decode("ascii"),
            "branch": payload["branch"],
        }
        expected_sha = payload.get("expected_sha")
        if expected_sha:
            body["sha"] = expected_sha
        result = _request_json(
            "PUT",
            f"/repos/{owner_q}/{repo_q}/contents/{encoded_path}",
            body,
        )
        content = result.get("content") if isinstance(result.get("content"), Mapping) else {}
        commit = result.get("commit") if isinstance(result.get("commit"), Mapping) else {}
        return {
            "content_sha": content.get("sha"),
            "commit_sha": commit.get("sha"),
            "commit_url": commit.get("html_url"),
        }
    if action == "pr_comment":
        result = _request_json(
            "POST",
            f"/repos/{owner_q}/{repo_q}/issues/{int(payload['pr_number'])}/comments",
            {"body": payload["comment"]},
        )
        return {"comment_id": result.get("id"), "comment_url": result.get("html_url")}
    raise ValueError(f"unsupported GitHub mutation provider action: {action}")


def _validate_repository(value: Any) -> str:
    repository = str(value or "").strip()
    if not _REPOSITORY_RE.fullmatch(repository):
        raise ValueError("repository must use owner/name format")
    if repository.startswith(".") or "/." in repository:
        raise ValueError("repository owner/name cannot begin with a dot")
    return repository


def _validate_branch(value: Any) -> str:
    branch = str(value or "").strip()
    if not _BRANCH_RE.fullmatch(branch) or ".." in branch or branch.endswith("/"):
        raise ValueError("invalid branch name")
    return branch


def _validate_repo_path(value: Any) -> str:
    raw = str(value or "").strip().replace("\\", "/")
    path = PurePosixPath(raw)
    if not raw or raw.startswith("/") or ".." in path.parts or "." in path.parts:
        raise ValueError("repository path must be a relative normalized path")
    if len(raw) > 512:
        raise ValueError("repository path is too long")
    folded = path.name.casefold()
    if folded.startswith(".env") and folded != ".env.example":
        raise ValueError("secret-bearing repository path is blocked")
    if folded in {"credentials.json", "client_secret.json", "secrets.json", "id_rsa", "id_ed25519"}:
        raise ValueError("secret-bearing repository path is blocked")
    if path.suffix.casefold() in {".key", ".p12", ".pfx"}:
        raise ValueError("secret-bearing repository path is blocked")
    return raw


def _plan_token(values: Mapping[str, Any]) -> str:
    canonical = json.dumps(dict(values), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


class GitHubWriteTools:
    def __init__(
        self,
        provider: GitHubMutationProvider = _default_provider,
        *,
        blocked_branches: tuple[str, ...] = ("main", "master", "stable", "production", "prod"),
        blocked_prefixes: tuple[str, ...] = ("release/", "deploy/"),
    ) -> None:
        if not callable(provider):
            raise ValueError("GitHub mutation provider must be callable")
        self.provider = provider
        self.blocked_branches = tuple(item.casefold() for item in blocked_branches)
        self.blocked_prefixes = tuple(item.casefold() for item in blocked_prefixes)

    def _guard_branch(self, branch: str) -> None:
        folded = branch.casefold()
        if folded in self.blocked_branches or any(folded.startswith(prefix) for prefix in self.blocked_prefixes):
            raise ValueError(f"protected GitHub branch is blocked by Phase 6 policy: {branch}")

    def file_upsert(self, payload: Mapping[str, Any], *, dry_run: bool) -> dict[str, Any]:
        repository = _validate_repository(payload.get("repository"))
        branch = _validate_branch(payload.get("branch"))
        self._guard_branch(branch)
        path = _validate_repo_path(payload.get("path"))
        content = payload.get("content")
        message = str(payload.get("message") or "").strip()
        if not isinstance(content, str):
            raise ValueError("GitHub file upsert requires string content")
        content_bytes = content.encode("utf-8")
        if len(content_bytes) > _MAX_CONTENT_BYTES:
            raise ValueError("GitHub file content exceeds 1 MiB Phase 6 limit")
        if not message or len(message) > 240:
            raise ValueError("commit message must contain 1-240 characters")
        expected_sha = str(payload.get("expected_sha") or "").strip() or None
        create = bool(payload.get("create", False))
        if create and expected_sha:
            raise ValueError("create=true cannot include expected_sha")
        if not create and not expected_sha:
            raise ValueError("updating an existing GitHub file requires expected_sha")
        if expected_sha and not _SHA_RE.fullmatch(expected_sha):
            raise ValueError("expected_sha must be a 40-character Git blob SHA")
        plan_values = {
            "repository": repository,
            "branch": branch,
            "path": path,
            "content_sha256": hashlib.sha256(content_bytes).hexdigest(),
            "message": message,
            "expected_sha": expected_sha,
            "create": create,
        }
        token = _plan_token(plan_values)
        plan = {
            "contract": GITHUB_WRITE_TOOLS_CONTRACT,
            **plan_values,
            "change_token": token,
            "write_action": "file_upsert",
            "merge": False,
            "release": False,
            "deployment": False,
            "applied": False,
        }
        if dry_run:
            return plan
        supplied = str(payload.get("change_token") or "").strip()
        if not supplied or supplied != token:
            raise ValueError("GitHub file upsert requires matching change_token from dry-run")
        result = self.provider(
            "file_upsert",
            {
                "repository": repository,
                "branch": branch,
                "path": path,
                "content": content,
                "message": message,
                "expected_sha": expected_sha,
                "create": create,
            },
        )
        if not isinstance(result, Mapping):
            raise TypeError("GitHub mutation provider must return a mapping")
        return {**plan, "applied": True, "result": dict(result)}

    def pr_comment(self, payload: Mapping[str, Any], *, dry_run: bool) -> dict[str, Any]:
        repository = _validate_repository(payload.get("repository"))
        pr_number = int(payload.get("pr_number") or 0)
        comment = payload.get("comment")
        if pr_number < 1:
            raise ValueError("pr_number must be positive")
        if not isinstance(comment, str) or not comment.strip():
            raise ValueError("pull request comment text is required")
        if len(comment) > _MAX_COMMENT_CHARS:
            raise ValueError("pull request comment exceeds Phase 6 limit")
        comment_sha256 = hashlib.sha256(comment.encode("utf-8")).hexdigest()
        plan_values = {"repository": repository, "pr_number": pr_number, "comment_sha256": comment_sha256}
        token = _plan_token(plan_values)
        plan = {
            "contract": GITHUB_WRITE_TOOLS_CONTRACT,
            **plan_values,
            "change_token": token,
            "write_action": "pr_comment",
            "code_changed": False,
            "pr_state_changed": False,
            "applied": False,
        }
        if dry_run:
            return plan
        supplied = str(payload.get("change_token") or "").strip()
        if not supplied or supplied != token:
            raise ValueError("GitHub PR comment requires matching change_token from dry-run")
        result = self.provider(
            "pr_comment",
            {"repository": repository, "pr_number": pr_number, "comment": comment},
        )
        if not isinstance(result, Mapping):
            raise TypeError("GitHub mutation provider must return a mapping")
        return {**plan, "applied": True, "result": dict(result)}

    def adapter(self, tool_id: str):
        if tool_id == "github.branch.file.upsert":
            def file_adapter(action: str, payload: Mapping[str, Any], dry_run: bool) -> Mapping[str, Any]:
                if action != "upsert":
                    raise ValueError(f"unsupported github.branch.file.upsert action: {action}")
                return self.file_upsert(payload, dry_run=dry_run)
            return file_adapter
        if tool_id == "github.pull_request.comment":
            def comment_adapter(action: str, payload: Mapping[str, Any], dry_run: bool) -> Mapping[str, Any]:
                if action != "comment":
                    raise ValueError(f"unsupported github.pull_request.comment action: {action}")
                return self.pr_comment(payload, dry_run=dry_run)
            return comment_adapter
        raise ValueError(f"unsupported GitHub write tool: {tool_id}")

    def status(self) -> dict[str, Any]:
        return {
            "contract": GITHUB_WRITE_TOOLS_CONTRACT,
            "tool_count": len(GITHUB_WRITE_TOOL_DEFINITIONS),
            "required_permission": "github.write",
            "network": True,
            "secret_access": True,
            "real_mutations_require_controller_approval": True,
            "change_token_required": True,
            "blocked_branches": list(self.blocked_branches),
            "blocked_prefixes": list(self.blocked_prefixes),
            "merge_available": False,
            "delete_available": False,
            "workflow_dispatch_available": False,
            "tag_available": False,
            "release_available": False,
            "deployment_available": False,
        }


def install_github_write_tools(
    registry: ToolRegistry,
    *,
    provider: GitHubMutationProvider = _default_provider,
    blocked_branches: tuple[str, ...] = ("main", "master", "stable", "production", "prod"),
    blocked_prefixes: tuple[str, ...] = ("release/", "deploy/"),
) -> GitHubWriteTools:
    pack = GitHubWriteTools(provider, blocked_branches=blocked_branches, blocked_prefixes=blocked_prefixes)
    for definition in GITHUB_WRITE_TOOL_DEFINITIONS:
        try:
            existing = registry.get(definition.tool_id)
        except ValueError:
            registry.register(definition)
        else:
            if asdict(existing) != asdict(definition):
                raise ValueError(f"GitHub write tool definition collision: {definition.tool_id}")
        try:
            registry.register_adapter(definition.tool_id, pack.adapter(definition.tool_id))
        except ValueError as exc:
            if "already registered" not in str(exc):
                raise
            registry.register_adapter(definition.tool_id, pack.adapter(definition.tool_id), replace=True)
    return pack
