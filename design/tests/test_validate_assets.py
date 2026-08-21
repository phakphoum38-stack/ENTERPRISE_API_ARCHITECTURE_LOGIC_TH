import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "design" / "manifest" / "assets.json"
VALIDATOR = ROOT / "design" / "validate_assets.py"


def run_validator():
    return subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def test_empty_manifest_is_valid():
    result = run_validator()
    assert result.returncode == 0, result.stdout + result.stderr


def test_manifest_schema_is_stable():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["schema"] == "research-os.gui-asset-manifest"
    assert isinstance(data["assets"], list)
