import tempfile
import unittest
from pathlib import Path

from house_brain import REQUIRED_FILES, analyze


class HouseBrainTests(unittest.TestCase):
    def test_missing_files_require_attention(self):
        with tempfile.TemporaryDirectory() as directory:
            status = analyze(Path(directory))
        self.assertEqual(status["health"], "needs-attention")
        self.assertEqual(status["required_files_present"], 0)
        self.assertEqual(len(status["missing"]), len(REQUIRED_FILES))

    def test_complete_house_is_healthy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in REQUIRED_FILES:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("ready\n", encoding="utf-8")
            artifacts = root / "research" / "artifacts"
            artifacts.mkdir(parents=True, exist_ok=True)
            (artifacts / "RES-001.md").write_text("knowledge\n", encoding="utf-8")
            (artifacts / "RES-002.md").write_text("knowledge\n", encoding="utf-8")

            status = analyze(root)

        self.assertEqual(status["health"], "healthy")
        self.assertEqual(status["score"], 90)
        self.assertEqual(status["knowledge_artifacts"], 2)
        self.assertEqual(status["missing"], [])


if __name__ == "__main__":
    unittest.main()
