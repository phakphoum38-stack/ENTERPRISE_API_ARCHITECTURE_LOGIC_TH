import unittest

from evidence_lineage import (
    DIRECT_PARENT,
    SQUASH_EQUIVALENT,
    SQUASH_RECONCILIATION,
    UNPROVEN,
    classify_lineage,
)


class EvidenceLineageTests(unittest.TestCase):
    def base(self, **overrides):
        data = {
            "pr_merged": True,
            "head_matches_pr": True,
            "merge_matches_pr": True,
            "parents": ["merge-parent"],
            "head_sha": "head",
            "original_base_sha": "original-base",
            "merge_parent_sha": "merge-parent",
            "original_base_is_ancestor_of_merge_parent": True,
            "head_tree_sha": "tree",
            "merge_tree_sha": "tree",
            "reconciliation_verified": False,
        }
        data.update(overrides)
        return data

    def test_direct_parent_remains_valid(self):
        mode, ok = classify_lineage(**self.base(parents=["head"], merge_parent_sha="head"))
        self.assertEqual((mode, ok), (DIRECT_PARENT, True))

    def test_advanced_base_squash_is_valid_when_tree_is_equivalent(self):
        mode, ok = classify_lineage(**self.base())
        self.assertEqual((mode, ok), (SQUASH_EQUIVALENT, True))

    def test_advanced_base_squash_is_valid_only_with_explicit_reconciliation(self):
        mode, ok = classify_lineage(
            **self.base(head_tree_sha="head-tree", merge_tree_sha="merge-tree", reconciliation_verified=True)
        )
        self.assertEqual((mode, ok), (SQUASH_RECONCILIATION, True))

    def test_tree_mismatch_without_reconciliation_fails_closed(self):
        mode, ok = classify_lineage(
            **self.base(head_tree_sha="head-tree", merge_tree_sha="merge-tree")
        )
        self.assertEqual((mode, ok), (UNPROVEN, False))

    def test_unrelated_merge_parent_fails_closed(self):
        mode, ok = classify_lineage(
            **self.base(original_base_is_ancestor_of_merge_parent=False)
        )
        self.assertEqual((mode, ok), (UNPROVEN, False))

    def test_multi_parent_merge_fails_closed(self):
        mode, ok = classify_lineage(
            **self.base(parents=["merge-parent", "other-parent"])
        )
        self.assertEqual((mode, ok), (UNPROVEN, False))

    def test_identity_mismatch_fails_closed(self):
        mode, ok = classify_lineage(**self.base(head_matches_pr=False))
        self.assertEqual((mode, ok), (UNPROVEN, False))


if __name__ == "__main__":
    unittest.main()
