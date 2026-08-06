import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("curator.py")
SPEC = importlib.util.spec_from_file_location("research_curator", MODULE_PATH)
assert SPEC and SPEC.loader
curator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(curator)


class ResearchCuratorTests(unittest.TestCase):
    def test_low_value_message_is_filtered(self):
        self.assertTrue(curator._is_low_value("ครับ"))
        self.assertLess(curator._knowledge_score("เยี่ยมครับ"), 0)

    def test_knowledge_sentence_scores_positive(self):
        sentence = "เราควรแยก Knowledge ออกจาก Renderer เพื่อให้เปลี่ยนการแสดงผลได้"
        self.assertGreater(curator._knowledge_score(sentence), 0)

    def test_relationship_parser(self):
        values = curator._parse_relationship(["supports:RES-20260806-ABCDEF12"])
        self.assertEqual(values[0].relation, "supports")
        self.assertEqual(values[0].target, "RES-20260806-ABCDEF12")

    def test_duplicate_detection(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            existing = output / "RES-20260806-EXISTING.md"
            existing.write_text(
                "---\nartifact_id: \"RES-20260806-EXISTING\"\n"
                "content_hash: \"sha256:abc\"\n---\n",
                encoding="utf-8",
            )
            self.assertEqual(
                curator._find_duplicate(output, "abc"),
                "RES-20260806-EXISTING",
            )

    def test_validated_promotion_requires_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.md"
            path.write_text(
                "---\nstatus: \"hypothesis\"\n"
                "updated_at: \"2026-08-06T00:00:00+00:00\"\n---\n\n"
                "## Evidence\n\n- ยังไม่มีรายการ\n",
                encoding="utf-8",
            )
            with self.assertRaises(SystemExit):
                curator._promote(path, "validated", [])


if __name__ == "__main__":
    unittest.main()
