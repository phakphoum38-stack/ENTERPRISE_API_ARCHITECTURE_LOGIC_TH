import json
import tempfile
import unittest
from pathlib import Path

from workspace_engine import Provenance, WorkspaceKnowledgeEngine


class WorkspaceKnowledgeEngineTests(unittest.TestCase):
    def test_workspace_boundary_incremental_index_search_and_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = WorkspaceKnowledgeEngine(tmp)
            alpha = engine.create_workspace("Alpha", workspace_id="alpha")
            beta = engine.create_workspace("Beta", workspace_id="beta")
            self.assertEqual(alpha["workspace_id"], "alpha")
            self.assertEqual(beta["workspace_id"], "beta")

            first = engine.upsert_record(
                "alpha",
                kind="document",
                title="Architecture Evidence",
                content="Research OS workspace knowledge evidence",
                provenance=Provenance(
                    source_type="document",
                    source_id="doc-1",
                    source_path="docs/architecture.md",
                    evidence=["ADR-001"],
                ),
                tags=["architecture"],
            )
            self.assertTrue(first["changed"])
            second = engine.upsert_record(
                "alpha",
                kind="document",
                title="Architecture Evidence",
                content="Research OS workspace knowledge evidence",
                provenance=Provenance(
                    source_type="document",
                    source_id="doc-1",
                    source_path="docs/architecture.md",
                    evidence=["ADR-001"],
                ),
                tags=["architecture"],
            )
            self.assertFalse(second["changed"])

            results = engine.search("alpha", "workspace evidence")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["provenance"]["source_id"], "doc-1")
            self.assertEqual(engine.search("beta", "workspace evidence"), [])

            restarted = WorkspaceKnowledgeEngine(tmp)
            self.assertEqual(len(restarted.search("alpha", "architecture")), 1)

    def test_duplicate_conflict_and_export_import_preserve_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            engine = WorkspaceKnowledgeEngine(root / "source")
            engine.create_workspace("Portable", workspace_id="portable")

            provenance = Provenance(
                source_type="sheet",
                source_id="schedule-1",
                source_path="drive/schedule.xlsx",
                evidence=["row:12"],
            )
            engine.upsert_record(
                "portable",
                kind="table",
                title="Schedule A",
                content="ER morning assignment",
                provenance=provenance,
                record_id="schedule-a",
            )
            engine.upsert_record(
                "portable",
                kind="table",
                title="Schedule A duplicate",
                content="ER morning assignment",
                provenance=Provenance(
                    source_type="sheet",
                    source_id="schedule-dup",
                    source_path="drive/schedule-copy.xlsx",
                ),
                record_id="schedule-duplicate",
            )
            engine.upsert_record(
                "portable",
                kind="table",
                title="Schedule conflict",
                content="ER evening assignment",
                provenance=provenance,
                record_id="schedule-conflict",
            )

            detected = engine.detect_duplicates_and_conflicts("portable")
            self.assertEqual(len(detected["duplicates"]), 1)
            self.assertEqual(len(detected["conflicts"]), 1)
            self.assertEqual(detected["conflicts"][0]["source_id"], "schedule-1")

            export_path = engine.export_workspace("portable", root / "portable.json")
            payload = json.loads(export_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)

            imported = WorkspaceKnowledgeEngine(root / "target")
            result = imported.import_workspace(export_path)
            self.assertEqual(result["records_imported"], 3)
            matches = imported.search("portable", "ER")
            self.assertEqual(len(matches), 3)
            source = next(item for item in matches if item["record_id"] == "schedule-a")
            self.assertEqual(source["provenance"]["source_path"], "drive/schedule.xlsx")
            self.assertEqual(source["provenance"]["evidence"], ["row:12"])


if __name__ == "__main__":
    unittest.main()
