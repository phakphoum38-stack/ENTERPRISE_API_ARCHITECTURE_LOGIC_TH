"""Fail-closed lineage classification for canonical evidence.

The PR's original base SHA is immutable provenance. A squash merge may legally
advance the target branch after the PR opens, so the original base need only be
an ancestor of the actual merge-time parent. Reconciliation is a separate,
explicit mode and never falls back to tree equivalence.
"""
from __future__ import annotations

from typing import Sequence


DIRECT_PARENT = "DIRECT_PARENT"
SQUASH_EQUIVALENT = "SQUASH_EQUIVALENT"
SQUASH_RECONCILIATION = "SQUASH_RECONCILIATION"
UNPROVEN = "UNPROVEN"


def classify_lineage(
    *,
    pr_merged: bool,
    head_matches_pr: bool,
    merge_matches_pr: bool,
    parents: Sequence[str],
    head_sha: str,
    original_base_sha: str,
    merge_parent_sha: str | None,
    original_base_is_ancestor_of_merge_parent: bool,
    head_tree_sha: str | None,
    merge_tree_sha: str | None,
    reconciliation_verified: bool = False,
) -> tuple[str, bool]:
    """Return (mode, lineage_ok) without weakening any identity checks."""
    identity_ok = pr_merged and head_matches_pr and merge_matches_pr
    if not identity_ok:
        return UNPROVEN, False

    if head_sha in parents:
        return DIRECT_PARENT, True

    if len(parents) != 1:
        return UNPROVEN, False
    if merge_parent_sha != parents[0] or not original_base_sha or not merge_parent_sha:
        return UNPROVEN, False
    if not original_base_is_ancestor_of_merge_parent:
        return UNPROVEN, False

    if head_tree_sha is not None and head_tree_sha == merge_tree_sha:
        return SQUASH_EQUIVALENT, True

    if reconciliation_verified:
        return SQUASH_RECONCILIATION, True

    return UNPROVEN, False
