from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.validate_architecture_completeness import inspect


class ArchitectureCompletenessInspectorTests(unittest.TestCase):
    def _fixture(self) -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "current").mkdir()
        (root / "packages/research_os_contracts/lib").mkdir(parents=True)
        for path in (
            "apps/research_os_flutter",
            "owner_special/flutter_app/lib",
            "v3/flutter_app",
        ):
            (root / path).mkdir(parents=True)
            (root / path / "pubspec.yaml").write_text(
                "dependencies:\n"
                "  research_os_contracts:\n"
                "    path: ../../packages/research_os_contracts\n",
                encoding="utf-8",
            )
        (root / "owner_special/flutter_app/lib/main.dart").write_text(
            "void main() {}\n", encoding="utf-8"
        )
        contract = json.loads(
            (Path(__file__).parents[1] / "current/ARCHITECTURE_COMPLETENESS_CONTRACT.json")
            .read_text(encoding="utf-8")
        )
        (root / "current/ARCHITECTURE_COMPLETENESS_CONTRACT.json").write_text(
            json.dumps(contract), encoding="utf-8"
        )
        for relative in contract["required_control_documents"]:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n", encoding="utf-8")
        for relative in contract["required_shared_contracts"].values():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n", encoding="utf-8")
        return root

    def test_current_repository_contract_is_complete(self) -> None:
        root = Path(__file__).parents[1]
        result = inspect(root)
        self.assertEqual(result["status"], "PASS", result["failures"])

    def test_missing_required_shared_contract_fails_closed(self) -> None:
        root = self._fixture()
        (root / "packages/research_os_contracts/lib/error_contract.dart").unlink()
        result = inspect(root)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(
            any(
                item["path"].endswith("error_contract.dart")
                for item in result["failures"]
            )
        )


if __name__ == "__main__":
    unittest.main()
