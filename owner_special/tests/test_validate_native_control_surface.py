import json
import tempfile
import unittest
from pathlib import Path

from tools.validate_native_control_surface import validate


class NativeControlSurfaceContractTests(unittest.TestCase):
    def test_contract_passes(self) -> None:
        root = Path(__file__).resolve().parents[2]
        result = validate(root / "current" / "NATIVE_CONTROL_SURFACE_CONTRACT.json")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(result["contract_sha256"]), 64)

    def test_authority_boundary_fails_closed(self) -> None:
        root = Path(__file__).resolve().parents[2]
        path = root / "current" / "NATIVE_CONTROL_SURFACE_CONTRACT.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["authority"]["may_merge"] = True
        with tempfile.TemporaryDirectory() as tmp:
            broken = Path(tmp) / "contract.json"
            broken.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                validate(broken)


if __name__ == "__main__":
    unittest.main()
