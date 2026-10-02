from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from tools.audit_workflow_order import scan_workflows, workflow_run_edges


class WorkflowRunAuditTests(unittest.TestCase):
    def test_workflow_run_edges_preserves_display_name(self) -> None:
        data = {
            "on": {
                "workflow_run": {
                    "workflows": ["Research OS Unified Windows Distribution"],
                    "types": ["completed"],
                }
            }
        }

        self.assertEqual(
            workflow_run_edges(data),
            ["Research OS Unified Windows Distribution"],
        )

    def test_scan_resolves_display_name_to_workflow_filename(self) -> None:
        with TemporaryDirectory() as raw:
            root = Path(raw)

            producer = root / "provenance-evidence-gate.yml"
            consumer = root / "research-os-release-spine-gate.yml"

            producer.write_text(
                """name: Provenance Evidence Gate

on:
  workflow_dispatch:
""",
                encoding="utf-8",
            )

            consumer.write_text(
                """name: Research OS Release Spine Gate

on:
  workflow_run:
    workflows:
      - Provenance Evidence Gate
    types:
      - completed
""",
                encoding="utf-8",
            )

            with patch("tools.audit_workflow_order.WORKFLOWS", root):
                records, edges, artifact_edges, errors = scan_workflows()

            self.assertEqual(errors, [])
            self.assertEqual(len(records), 2)

            self.assertIn(
                {
                    "from": "provenance-evidence-gate.yml",
                    "to": "research-os-release-spine-gate.yml",
                    "type": "workflow_run",
                },
                edges,
            )


if __name__ == "__main__":
    unittest.main()
