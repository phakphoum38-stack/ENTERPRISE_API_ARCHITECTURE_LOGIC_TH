"""Regression tests for the Research OS API import boundary."""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "tools" / "research_os_api"


class ResearchOSImportBoundaryTests(unittest.TestCase):
    def test_render_server_imports_from_api_working_directory_without_pythonpath(self) -> None:
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        result = subprocess.run(
            [
                sys.executable,
                "-u",
                "-c",
                "import render_server; print('RENDER_SERVER_IMPORT=PASS')",
            ],
            cwd=API_DIR,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=f"render_server import failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}",
        )
        self.assertIn("RENDER_SERVER_IMPORT=PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
