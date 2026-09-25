import unittest
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "audit_research_os_ux_legacy",
    ROOT / "tools/audit_research_os_ux_legacy.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class UXLegacyAuditTest(unittest.TestCase):
    def test_primary_surfaces_are_present_and_clean(self):
        self.assertEqual(MODULE.audit(), [])


if __name__ == "__main__":
    unittest.main()
