#!/usr/bin/env python3
"""Verify that all non-self PR checks for an exact HEAD are terminal and green."""
from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

PASS_CONCLUSIONS = {"success", "neutral", "skipped"}
PENDING_STATUSES = {"queued", "in_progress", "pending", "requested", "waiting"}
TRANSIENT_HTTP_STATUS = {429, 500, 502, 503, 504}


def headers() -> dict[str, str]:
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    result = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "aeos-pr-check-verifier",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        result["Authorization"] = "Bearer " + token
    return result


def permission_hint(url: str) -> str | None:
    if "/check-runs" in url:
        return "ensure the workflow token has checks: read permission"
    if "/status" in url:
        return "ensure the workflow token has statuses: read permission"
    return None


def request_json(url: str, *, retries: int = 3, timeout: int = 20) -> tuple[Any, dict[str, str]]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        request = urllib.request.Request(url, headers=headers(), method="GET")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return payload, dict(response.headers.items())
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            hint = permission_hint(url)
            if exc.code in TRANSIENT_HTTP_STATUS and attempt < retries:
                time.sleep(attempt)
                last_error = RuntimeError(f"transient GitHub HTTP {exc.code}: {body[:300]}")
                continue
            if exc.code == 403 and hint:
                raise RuntimeError(f"GitHub HTTP 403: {hint}. Response: {body[:300]}") from exc
            raise RuntimeError(f"GitHub HTTP {exc.code}: {body[:300]}") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            if attempt < retries:
                time.sleep(attempt)
                last_error = exc
                continue
            raise RuntimeError(f"GitHub request failed: {exc}") from exc
    raise RuntimeError(f"GitHub request failed after retries: {last_error}")


def paginate(url: str, item_key: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    next_url: str | None = url
    while next_url:
        payload, response_headers = request_json(next_url)
        page_items = payload.get(item_key, []) if isinstance(payload, dict) else []
        items.extend(item for item in page_items if isinstance(item, dict))
        link = response_headers.get("Link", "")
        next_url = None
        for part in link.split(","):
            if 'rel="next"' not in part:
                continue
            start = part.find("<")
            end = part.find(">", start + 1)
            if start != -1 and end != -1:
                next_url = part[start + 1 : end]
                break
    return items


def is_self_check(check: dict[str, Any], current_run_id: str) -> bool:
    url = str(check.get("details_url") or check.get("html_url") or check.get("target_url") or "")
    if not current_run_id:
        return False
    return re.search(rf"/actions/runs/{re.escape(current_run_id)}(?:$|[/?#])", url) is not None


def normalize_check_run(check: dict[str, Any], current_run_id: str) -> dict[str, Any] | None:
    if is_self_check(check, current_run_id):
        return None
    status = str(check.get("status") or "").lower()
    conclusion = str(check.get("conclusion") or "").lower()
    if status != "completed":
        bucket = "pending"
        state = status.upper() or "UNKNOWN"
    elif conclusion in PASS_CONCLUSIONS:
        bucket = "pass"
        state = conclusion.upper()
    else:
        bucket = "fail"
        state = conclusion.upper() or "FAILED"
    return {
        "source": "check_run",
        "name": check.get("name"),
        "bucket": bucket,
        "state": state,
        "details_url": check.get("details_url") or check.get("html_url"),
    }


def normalize_status_context(status: dict[str, Any], current_run_id: str) -> dict[str, Any] | None:
    if is_self_check(status, current_run_id):
        return None
    state = str(status.get("state") or "").lower()
    if state == "success":
        bucket = "pass"
    elif state in PENDING_STATUSES:
        bucket = "pending"
    else:
        bucket = "fail"
    return {
        "source": "status",
        "name": status.get("context"),
        "bucket": bucket,
        "state": state.upper() or "UNKNOWN",
        "details_url": status.get("target_url"),
    }


def summarize(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "source": check.get("source"),
            "name": check.get("name"),
            "state": check.get("state"),
            "bucket": check.get("bucket"),
            "details_url": check.get("details_url"),
        }
        for check in checks
    ]


def classify(checks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pending = [check for check in checks if check.get("bucket") == "pending"]
    bad = [check for check in checks if check.get("bucket") == "fail"]
    return pending, bad


def fetch_external_checks(repository: str, head_sha: str, current_run_id: str) -> list[dict[str, Any]]:
    repo_path = urllib.parse.quote(repository, safe="/")
    ref = urllib.parse.quote(head_sha, safe="")
    check_runs = paginate(
        f"https://api.github.com/repos/{repo_path}/commits/{ref}/check-runs?per_page=100",
        "check_runs",
    )
    statuses = paginate(
        f"https://api.github.com/repos/{repo_path}/commits/{ref}/status?per_page=100",
        "statuses",
    )
    external: list[dict[str, Any]] = []
    for item in check_runs:
        normalized = normalize_check_run(item, current_run_id)
        if normalized:
            external.append(normalized)
    for item in statuses:
        if not isinstance(item, dict):
            continue
        normalized = normalize_status_context(item, current_run_id)
        if normalized:
            external.append(normalized)
    return external


def poll_interval(attempt: int, initial_seconds: int, max_seconds: int) -> int:
    exponent = min((max(1, attempt) - 1) // 3, 3)
    return min(max_seconds, initial_seconds * (2**exponent))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--head-sha", required=True)
    parser.add_argument(
        "--initial-poll-seconds",
        type=int,
        default=int(os.environ.get("INITIAL_POLL_SECONDS", "5")),
    )
    parser.add_argument(
        "--max-poll-seconds",
        type=int,
        default=int(os.environ.get("MAX_POLL_SECONDS", "30")),
    )
    parser.add_argument(
        "--max-wait-seconds",
        type=int,
        default=int(os.environ.get("MAX_WAIT_SECONDS", "900")),
    )
    parser.add_argument("--current-run-id", default=os.environ.get("GITHUB_RUN_ID", ""))
    args = parser.parse_args()

    if not args.repository:
        raise SystemExit("repository is required")
    if args.initial_poll_seconds < 1 or args.max_poll_seconds < args.initial_poll_seconds:
        raise SystemExit("invalid poll interval configuration")
    if args.max_wait_seconds < 1:
        raise SystemExit("max wait must be positive")

    deadline = time.monotonic() + args.max_wait_seconds
    attempt = 0
    last_signature: str | None = None

    while True:
        attempt += 1
        checks = fetch_external_checks(args.repository, args.head_sha, args.current_run_id)
        pending, bad = classify(checks)

        if bad:
            print(json.dumps({"status": "EXTERNAL_CI_FAILED", "failing_checks": summarize(bad)}, indent=2))
            raise SystemExit("one or more external PR checks are not passing")

        if checks and not pending:
            print(
                json.dumps(
                    {
                        "status": "ALL_EXTERNAL_CHECKS_PASS",
                        "check_count": len(checks),
                        "checks": summarize(checks),
                    },
                    indent=2,
                )
            )
            return 0

        remaining = max(0, int(deadline - time.monotonic()))
        if remaining <= 0:
            payload = {
                "status": "WAITING_FOR_EXTERNAL_CI" if pending else "WAITING_FOR_EXTERNAL_CI_REGISTRATION",
                "poll": attempt,
                "pending_count": len(pending),
                "pending_checks": summarize(pending),
                "observed_check_count": len(checks),
            }
            print(json.dumps(payload, indent=2))
            raise SystemExit("external PR checks did not reach a passing terminal state before timeout")

        payload = {
            "status": "WAITING_FOR_EXTERNAL_CI" if pending else "WAITING_FOR_EXTERNAL_CI_REGISTRATION",
            "poll": attempt,
            "observed_check_count": len(checks),
            "pending_count": len(pending),
            "pending_checks": summarize(pending),
            "seconds_remaining": remaining,
        }
        signature = json.dumps(payload, sort_keys=True)
        if signature != last_signature:
            print(json.dumps(payload, indent=2))
            last_signature = signature

        time.sleep(min(poll_interval(attempt, args.initial_poll_seconds, args.max_poll_seconds), remaining))


if __name__ == "__main__":
    raise SystemExit(main())
