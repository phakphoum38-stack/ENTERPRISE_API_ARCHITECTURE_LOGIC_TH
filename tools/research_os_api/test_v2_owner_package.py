#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from v2_owner_package import (
    OWNER_PACKAGE_FILES,
    OwnerPackageError,
    export_owner_package,
    validate_paths,
    validate_source_tree,
)


_REPO_ROOT = Path(__file__).resolve().parents[2]


class OwnerPackageTests(unittest.TestCase):
    def test_repository_owner_source_is_clean_and_exact_allowlist(self) -> None:
        report = validate_source_tree(_REPO_ROOT)
        self.assertTrue(report["validated"])
        self.assertFalse(report["forbidden_content_found"])
        self.assertEqual(report["files"], list(OWNER_PACKAGE_FILES))

    def test_owner_package_rejects_any_extra_file(self) -> None:
        with self.assertRaisesRegex(OwnerPackageError, "unexpected owner-package files"):
            validate_paths((*OWNER_PACKAGE_FILES, "tools/research_os_api/extra.py"))

    def test_owner_package_rejects_forbidden_external_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / OWNER_PACKAGE_FILES[0]
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("reference = 'https://example.invalid'\n", encoding="utf-8")
            with self.assertRaisesRegex(OwnerPackageError, "forbidden external-content markers"):
                validate_source_tree(root)

    def test_export_contains_only_allowlisted_runtime_file_plus_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "owner-package"
            report = export_owner_package(_REPO_ROOT, destination)
            self.assertTrue(report["validated"])
            exported = sorted(
                path.relative_to(destination).as_posix()
                for path in destination.rglob("*")
                if path.is_file()
            )
        self.assertEqual(
            exported,
            sorted([*OWNER_PACKAGE_FILES, "OWNER_PACKAGE_MANIFEST.json"]),
        )


if __name__ == "__main__":
    unittest.main()
