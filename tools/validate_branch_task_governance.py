from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current" / "BRANCH_TASK_GOVERNANCE.yml"
DOCUMENT = ROOT / "current" / "BRANCH_TASK_GOVERNANCE.md"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
TASK_BRANCH_RE = re.compile(r"^(?:task|fix|feat|security|release)/[^/]+-[^/]+$")


def main() -> None:
    assert CONTRACT.is_file(), "branch/task governance contract is missing"
    assert DOCUMENT.is_file(), "branch/task governance document is missing"

    data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8")) or {}
    text = DOCUMENT.read_text(encoding="utf-8")

    required_states = {
        "CREATED", "ACTIVE", "RUNNING", "VERIFIED", "FROZEN",
        "MERGE_CANDIDATE", "MERGED", "QUARANTINED", "ARCHIVED",
    }
    states = set(data.get("states") or [])
    assert states == required_states, "governance lifecycle states are incomplete"

    required_fields = {
        "task_id", "purpose", "repository", "branch", "base_branch",
        "base_sha", "parent_task", "head_sha", "state",
    }
    assert set(data.get("required_task_fields") or []) == required_fields, (
        "required task fields must remain canonical"
    )

    rules = data.get("rules") or {}
    for rule in (
        "one_task_one_branch",
        "exact_base_sha_required",
        "exact_head_sha_required",
        "running_branch_is_locked",
        "failed_branch_becomes_quarantined",
        "quarantined_branch_cannot_be_implicit_base",
        "unknown_state_cannot_be_base",
        "unknown_base_sha_cannot_be_base",
        "merge_requires_exact_head_evidence",
        "merge_requires_explicit_authorization",
        "governance_validation_is_read_only",
    ):
        assert rules.get(rule) is True, f"governance rule missing or disabled: {rule}"

    active = data.get("current_active_review") or {}
    for field in ("task_id", "branch", "base_branch", "base_sha", "head_sha", "state"):
        assert active.get(field) not in (None, ""), f"active review missing {field}"

    assert SHA_RE.fullmatch(str(active["base_sha"])), "base_sha must be an exact SHA"
    assert SHA_RE.fullmatch(str(active["head_sha"])), "head_sha must be an exact SHA"
    assert active["branch"] not in set(data.get("ambiguous_names") or []), (
        "ambiguous branch name cannot be the active review branch"
    )
    assert active["state"] in states

    protected = set(data.get("protected_refs") or [])
    assert active["branch"] not in protected or active["branch"] == "computer-use-boundary"
    assert "A branch name or document alone is not proof of correctness." in text
    assert "UNKNOWN branch state" in text
    assert "Merge Status UI" in text

    for name in data.get("active_branch_prefixes") or []:
        assert name.endswith("/"), f"active branch prefix must end with '/': {name}"

    # Validate the naming rule against the canonical examples in the document.
    for example in ("task/256-branch-isolation", "fix/257-merge-evidence"):
        assert TASK_BRANCH_RE.fullmatch(example), f"invalid canonical branch example: {example}"

    print("Branch/task governance contract validation passed.")


if __name__ == "__main__":
    main()
