#!/usr/bin/env python3
"""Read-only GitHub dashboard adapter for Research OS.

The adapter keeps GitHub credentials on the API side. Public repositories work
without a token; private repositories require RESEARCH_OS_GITHUB_TOKEN or
GITHUB_TOKEN. Only compact dashboard fields are returned.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class GitHubStatusError(RuntimeError):
    pass


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "research-os-api",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("RESEARCH_OS_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get_json(path: str) -> Any:
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        headers=_headers(),
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GitHubStatusError(f"GitHub HTTP {exc.code}: {body[:300]}") from exc
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise GitHubStatusError(f"GitHub request failed: {exc}") from exc


def _repo_path(repository: str, suffix: str = "") -> str:
    owner, separator, name = repository.partition("/")
    if not separator or not owner or not name or "/" in name:
        raise ValueError("repository must use owner/name format")
    encoded_owner = urllib.parse.quote(owner, safe="")
    encoded_name = urllib.parse.quote(name, safe="")
    return f"/repos/{encoded_owner}/{encoded_name}{suffix}"


def dashboard(repository: str) -> dict[str, Any]:
    repo = _get_json(_repo_path(repository))
    commits = _get_json(_repo_path(repository, "/commits?per_page=5"))
    pulls = _get_json(_repo_path(repository, "/pulls?state=open&per_page=5"))
    runs = _get_json(_repo_path(repository, "/actions/runs?per_page=5"))

    if not isinstance(repo, dict):
        raise GitHubStatusError("GitHub repository response has an invalid shape")

    commit_items = []
    for item in commits if isinstance(commits, list) else []:
        commit = item.get("commit", {}) if isinstance(item, dict) else {}
        author = commit.get("author", {}) if isinstance(commit, dict) else {}
        commit_items.append(
            {
                "sha": str(item.get("sha", ""))[:7],
                "message": str(commit.get("message", "")).splitlines()[0],
                "author": str(author.get("name", "")),
                "date": author.get("date"),
                "url": item.get("html_url"),
            }
        )

    pull_items = []
    for item in pulls if isinstance(pulls, list) else []:
        pull_items.append(
            {
                "number": item.get("number"),
                "title": item.get("title"),
                "author": (item.get("user") or {}).get("login"),
                "draft": bool(item.get("draft")),
                "url": item.get("html_url"),
            }
        )

    workflow_runs = runs.get("workflow_runs", []) if isinstance(runs, dict) else []
    run_items = []
    for item in workflow_runs:
        run_items.append(
            {
                "name": item.get("name"),
                "status": item.get("status"),
                "conclusion": item.get("conclusion"),
                "branch": item.get("head_branch"),
                "event": item.get("event"),
                "updated_at": item.get("updated_at"),
                "url": item.get("html_url"),
            }
        )

    return {
        "repository": repository,
        "default_branch": repo.get("default_branch"),
        "visibility": repo.get("visibility", "private" if repo.get("private") else "public"),
        "open_issues_count": repo.get("open_issues_count", 0),
        "watchers_count": repo.get("subscribers_count", repo.get("watchers_count", 0)),
        "forks_count": repo.get("forks_count", 0),
        "updated_at": repo.get("updated_at"),
        "url": repo.get("html_url"),
        "commits": commit_items,
        "pull_requests": pull_items,
        "workflow_runs": run_items,
        "credential_configured": bool(
            os.getenv("RESEARCH_OS_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
        ),
        "read_only": True,
    }
