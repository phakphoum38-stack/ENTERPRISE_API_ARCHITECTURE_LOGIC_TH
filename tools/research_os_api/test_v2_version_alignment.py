from __future__ import annotations

import re
import unittest
from pathlib import Path


class V2VersionAlignmentTests(unittest.TestCase):
    def test_flutter_installer_and_openapi_share_dev_version(self) -> None:
        root = Path(__file__).resolve().parents[2]
        pubspec = (root / "apps/research_os_flutter/pubspec.yaml").read_text(encoding="utf-8")
        installer = (root / "installer/research-os.iss").read_text(encoding="utf-8")
        openapi = (root / "tools/research_os_api/openapi.yaml").read_text(encoding="utf-8")

        flutter_full = re.search(r"^version:\s*(\S+)", pubspec, re.MULTILINE)
        installer_match = re.search(r'#define MyAppVersion "([^"]+)"', installer)
        openapi_match = re.search(
            r"^info:\s*\n(?:.*\n)*?\s+version:\s*([^\s]+)",
            openapi,
            re.MULTILINE,
        )
        self.assertIsNotNone(flutter_full)
        self.assertIsNotNone(installer_match)
        self.assertIsNotNone(openapi_match)

        flutter_version = flutter_full.group(1).split("+", 1)[0]
        installer_version = installer_match.group(1)
        api_version = openapi_match.group(1)
        self.assertEqual(flutter_version, "2.0.0-dev.1")
        self.assertEqual(installer_version, flutter_version)
        self.assertEqual(api_version, flutter_version)


if __name__ == "__main__":
    unittest.main()
