from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
AUDITOR_PATH = REPO_ROOT / "tools" / "file_audit_v6x6.py"


def _load_auditor():
    spec = importlib.util.spec_from_file_location("file_audit_v6x6", AUDITOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load 6^6 file auditor: {AUDITOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
