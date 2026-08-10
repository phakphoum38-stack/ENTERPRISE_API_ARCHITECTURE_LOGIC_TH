#!/usr/bin/env python3
"""Governed read-only GitHub tools for Research OS AI Brain.

Phase 5 wraps the existing compact GitHub dashboard provider in an explicit
ToolDefinition. The adapter is networked and may use an API-side credential, so
it is marked ``secret_access`` and must pass the existing github.read permission
and Phase 4 secret-aware execution boundary before invocation.

This module does not expose arbitrary URLs, shell commands, repository writes,
workflow dispatch, merge, release or deployment actions.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import asdict
from typing import Any

from github_status import dashboard as github_dashboard
from v2_tool_registry import ToolDefinition, ToolRegistry


GITHUB_READ_TOOLS_CONTRACT = "brain-github-read-tools-phase-5"
_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}$")
GitHubDashboardProvider = Callable[[str], Mapping[str, Any]]


GITHUB_READ_TOOL_DEFINITIONS: tuple[ToolDefinition, ...] = (
    ToolDefinition(
        "github.repository.dashboard",
        "1.0.0",
        "GitHub Repository Dashboard",
        "Reads compact repository, commit, pull-request and workflow-run status from GitHub.",
        (
            "github_read",
            "github_repository_read",
            "github_commit_read",
            "github_pull_request_read",
            "github_workflow_status_read",
        ),
        permissions=("github.read",),
        mutating=False,
        destructive=False,
        network=True,
        secret_access=True,
        idempotent=True,
        supports_dry_run=True,
    ),
)


def _validate_repository(value: Any) -> str:
    repository = str(value or "").strip()
    if not _REPOSITORY_RE.fullmatch(repository):
        raise ValueError("repository must use owner/name format")
    if repository.startswith(".") or "/." in repository:
        raise ValueError("repository owner/name cannot begin with a dot")
    return repository


class GitHubReadTools:
    def __init__(self, provider: GitHubDashboardProvider = github_dashboard) -> None:
        if not callable(provider):
            raise ValueError("GitHub dashboard provider must be callable")
        self.provider = provider

    def repository_dashboard(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        repository = _validate_repository(payload.get("repository"))
        raw = self.provider(repository)
        if not isinstance(raw, Mapping):
            raise TypeError("GitHub dashboard provider must return a mapping")
        result = dict(raw)
        # Contract-owned fields override provider output so callers can rely on
        # read-only semantics even when a test/custom provider omits them.
        result.update(
            {
                "contract": GITHUB_READ_TOOLS_CONTRACT,
                "repository": repository,
                "read_only": True,
                "write_actions_available": False,
            }
        )
        return result

    def adapter(self, tool_id: str):
        if tool_id != "github.repository.dashboard":
            raise ValueError(f"unsupported GitHub read tool: {tool_id}")

        def invoke(action: str, payload: Mapping[str, Any], dry_run: bool) -> Mapping[str, Any]:
            del dry_run
            if action != "dashboard":
                raise ValueError(f"unsupported {tool_id} action: {action}")
            return self.repository_dashboard(payload)

        return invoke

    @staticmethod
    def status() -> dict[str, Any]:
        return {
            "contract": GITHUB_READ_TOOLS_CONTRACT,
            "tool_count": len(GITHUB_READ_TOOL_DEFINITIONS),
            "read_only": True,
            "network": True,
            "secret_access": True,
            "required_permission": "github.read",
            "arbitrary_url_access": False,
            "write_actions_available": False,
        }


def install_github_read_tools(
    registry: ToolRegistry,
    *,
    provider: GitHubDashboardProvider = github_dashboard,
) -> GitHubReadTools:
    """Install the explicit read-only GitHub tool pack into one Brain registry.

    Definitions are collision checked; existing adapters for this exact contract
    are replaceable so tests/runtime composition can inject a bounded provider.
    """

    pack = GitHubReadTools(provider)
    for definition in GITHUB_READ_TOOL_DEFINITIONS:
        try:
            existing = registry.get(definition.tool_id)
        except ValueError:
            registry.register(definition)
        else:
            if asdict(existing) != asdict(definition):
                raise ValueError(f"GitHub tool definition collision: {definition.tool_id}")
        try:
            registry.register_adapter(definition.tool_id, pack.adapter(definition.tool_id))
        except ValueError as exc:
            if "already registered" not in str(exc):
                raise
            registry.register_adapter(
                definition.tool_id,
                pack.adapter(definition.tool_id),
                replace=True,
            )
    return pack
