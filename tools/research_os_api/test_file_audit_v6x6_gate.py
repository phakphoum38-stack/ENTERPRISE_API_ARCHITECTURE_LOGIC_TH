from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
AUDITOR_PATH = REPO_ROOT / "tools" / "file_audit_v6x6.py"
MODULE_NAME = "file_audit_v6x6"


def _load_auditor():
    spec = importlib.util.spec_from_file_location(MODULE_NAME, AUDITOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load 6^6 file auditor: {AUDITOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(MODULE_NAME, None)
        raise
    return module


@unittest.skipIf(
    os.getenv("RESEARCH_OS_SKIP_FILE_AUDIT") == "1",
    "6^6 repository audit runs in its dedicated Candidate gate",
)
class CandidateFileAuditV6x6GateTests(unittest.TestCase):
    def test_candidate_repository_passes_adaptive_6x6_file_audit(self) -> None:
        auditor = _load_auditor()
        report = auditor.audit_repository(REPO_ROOT)

        self.assertEqual(report["contract"], "adaptive-file-audit-v6x6")
        self.assertEqual(report["capacity"]["branching_factor"], 6)
        self.assertEqual(report["capacity"]["depth"], 6)
        self.assertEqual(report["capacity"]["max_leaf_capacity"], 46656)
        self.assertGreater(report["files_scanned"], 0)

        errors = [item for item in report["findings"] if item["severity"] == "error"]
        if errors:
            details = "\n".join(
                f"{item['path']} [{item['code']}]: {item['message']}" for item in errors[:100]
            )
            self.fail(
                "Candidate 6^6 file audit found blocking errors "
                f"({len(errors)} total):\n{details}"
            )


if __name__ == "__main__":
    unittest.main()
